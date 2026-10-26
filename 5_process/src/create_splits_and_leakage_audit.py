from pathlib import Path
import pandas as pd, json, re, unicodedata
import matplotlib.pyplot as plt
from rapidfuzz import process, fuzz
ROOT=Path(__file__).resolve().parents[2]
CSV=ROOT/'1_du_lieu_chinh/vn_labor_news_dataset.csv'
R=ROOT/'5_process/reports'; S=ROOT/'5_process/splits'
CHARTS=R/'charts'
for p in (R,S,CHARTS): p.mkdir(parents=True,exist_ok=True)
df=pd.read_csv(CSV,low_memory=False,encoding='utf-8-sig',dtype={'article_id':str})
required={'article_id','publish_date','source_name','topic_primary','title','content','location'}
missing=required-set(df.columns)
if missing:
    raise ValueError(f'Missing required input columns: {sorted(missing)}')
if df['article_id'].isna().any() or not df['article_id'].is_unique:
    raise ValueError('article_id must be present and unique.')
df['publish_date']=pd.to_datetime(df['publish_date'],errors='coerce')
if df['publish_date'].isna().any():
    raise ValueError('publish_date contains missing or unparsable values.')
if df['topic_primary'].isna().any() or df['source_name'].isna().any():
    raise ValueError('source_name and topic_primary must be populated for this manifest.')
# Default decision for completion: topic_primary as explicitly weak-label target; temporal splits as proposed.
def split_date(d):
    if d < pd.Timestamp('2025-01-01'): return 'train'
    if d < pd.Timestamp('2026-01-01'): return 'validation'
    return 'test'
df['split']=df['publish_date'].map(split_date)
# Split manifests: minimal IDs + audit metadata, no feature matrix and no training.
manifest=df[['article_id','publish_date','source_name','topic_primary','split']].copy()
manifest['publish_date']=manifest['publish_date'].dt.strftime('%Y-%m-%d')
manifest.to_csv(S/'split_manifest.csv',index=False,encoding='utf-8-sig')
for split in ['train','validation','test']:
    manifest[manifest.split==split].to_csv(S/f'{split}_manifest.csv',index=False,encoding='utf-8-sig')
# Normalize titles for candidate fuzzy duplicate audit.
def norm(s):
    s=unicodedata.normalize('NFKC',str(s or '')).casefold()
    s=re.sub(r'https?://\S+',' ',s)
    s=re.sub(r'[^\w\s]',' ',s,flags=re.UNICODE)
    return re.sub(r'\s+',' ',s).strip()
titles=[norm(x) for x in df['title'].fillna('')]
# block candidate comparisons by first token + length bucket to reduce comparisons; then rapidfuzz within blocks
blocks={}
for i,t in enumerate(titles):
    toks=t.split(); key=(toks[0][:5] if toks else '', len(t)//25)
    blocks.setdefault(key,[]).append(i)
pairs=[]; seen=set()
for inds in blocks.values():
    if len(inds)<2: continue
    vals=[titles[i] for i in inds]
    for pos,i in enumerate(inds):
        # candidate comparisons only within conservative block; title similarity is a screening signal, not a final duplicate verdict
        matches=process.extract(titles[i], vals, scorer=fuzz.ratio, score_cutoff=90, limit=8)
        for _,score,jpos in matches:
            j=inds[jpos]
            if j<=i or i==j: continue
            pair=(i,j)
            if pair in seen: continue
            seen.add(pair)
            pairs.append({'article_id_1':df.iloc[i]['article_id'],'article_id_2':df.iloc[j]['article_id'],
                          'title_1':df.iloc[i]['title'],'title_2':df.iloc[j]['title'],
                          'similarity_score':round(float(score),2),'date_1':df.iloc[i]['publish_date'].strftime('%Y-%m-%d'),
                          'date_2':df.iloc[j]['publish_date'].strftime('%Y-%m-%d'),'source_1':df.iloc[i]['source_name'],
                          'source_2':df.iloc[j]['source_name'],'split_1':df.iloc[i]['split'],'split_2':df.iloc[j]['split'],
                          'cross_split':df.iloc[i]['split']!=df.iloc[j]['split'],'review_status':'manual_review_required'})
pairs_df=pd.DataFrame(pairs)
if pairs_df.empty:
    pairs_df=pd.DataFrame(columns=['article_id_1','article_id_2','title_1','title_2','similarity_score','date_1','date_2','source_1','source_2','split_1','split_2','cross_split','review_status'])
pairs_df.to_csv(R/'near_duplicate_title_candidates.csv',index=False,encoding='utf-8-sig')
# split stats and hard validation
split_counts=df['split'].value_counts().to_dict()
checks={
 'csv_rows':int(len(df)), 'manifest_rows':int(len(manifest)), 'split_counts':{k:int(split_counts.get(k,0)) for k in ['train','validation','test']},
 'split_counts_sum_to_csv':int(sum(split_counts.values()))==len(df),
 'manifest_article_ids_unique':bool(manifest.article_id.is_unique),
 'no_missing_split':bool(df['split'].notna().all()),
 'date_ranges':{},
 'near_duplicate_candidate_pairs':int(len(pairs_df)),
 'near_duplicate_candidates_cross_split':int(pairs_df.cross_split.sum()) if len(pairs_df) else 0,
 'near_duplicate_method':'Fuzzy title ratio >=90 within first-token/length blocks; candidate screening only, not exhaustive and not a confirmed duplicate classification.'
}
metadata_path=ROOT/'5_process'/'data'/'interim'/'metadata_clean.parquet'
cluster_cross_split=[]
if metadata_path.exists():
    metadata=pd.read_parquet(metadata_path,columns=['article_id','dup_cluster_id'])
    if metadata['article_id'].isna().any() or not metadata['article_id'].is_unique:
        raise ValueError('Metadata article_id must be present and unique.')
    if set(metadata['article_id']) != set(manifest['article_id']):
        raise ValueError('Metadata article IDs do not exactly match the source dataset.')
    clustered=metadata.merge(manifest[['article_id','split']],on='article_id',how='left',validate='one_to_one')
    cluster_stats=clustered[clustered['dup_cluster_id'].notna()].groupby('dup_cluster_id').agg(
        article_count=('article_id','size'),
        split_count=('split','nunique'),
        splits=('split',lambda values:'; '.join(sorted(set(values.dropna())))),
        article_ids=('article_id',lambda values:'; '.join(values)),
    )
    cluster_cross_split=cluster_stats[cluster_stats['split_count']>1].reset_index().to_dict('records')
review_reasons={}
for row in pairs_df[pairs_df['cross_split']].to_dict('records'):
    for article_id in (row['article_id_1'],row['article_id_2']):
        review_reasons.setdefault(article_id,set()).add('cross_split_title_candidate')
for row in cluster_cross_split:
    for article_id in row['article_ids'].split('; '):
        review_reasons.setdefault(article_id,set()).add(f"cross_split_metadata_cluster:{row['dup_cluster_id']}")
eligibility=manifest.copy()
eligibility['modeling_split']=eligibility['split']
eligibility['hold_reason']=eligibility['article_id'].map(
    lambda article_id:'; '.join(sorted(review_reasons.get(article_id,set())))
)
held_ids=set(review_reasons)
eligibility.loc[eligibility['article_id'].isin(held_ids),'modeling_split']='review_hold'
eligibility.to_csv(S/'modeling_eligibility_manifest.csv',index=False,encoding='utf-8-sig')
eligible_counts=eligibility.loc[eligibility['modeling_split'].isin(['train','validation','test']),'modeling_split'].value_counts().to_dict()
eligible_ids=set(eligibility.loc[eligibility['modeling_split']!='review_hold','article_id'])
if any(
    row['article_id_1'] in eligible_ids and row['article_id_2'] in eligible_ids
    for row in pairs_df[pairs_df['cross_split']].to_dict('records')
):
    raise ValueError('A known cross-split title candidate remains eligible for modeling.')
checks['modeling_review_hold_rows']=len(held_ids)
checks['modeling_eligible_split_counts']={k:int(eligible_counts.get(k,0)) for k in ['train','validation','test']}
checks['known_cross_split_title_candidates_quarantined']=True
checks['metadata_duplicate_clusters_cross_split']=len(cluster_cross_split)
checks['metadata_duplicate_cluster_audit_available']=metadata_path.exists()
for name in ['train','validation','test']:
 x=df[df.split==name]
 checks['date_ranges'][name]={'min':x.publish_date.min().strftime('%Y-%m-%d'),'max':x.publish_date.max().strftime('%Y-%m-%d'),'rows':int(len(x))}
(R/'split_and_leakage_checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
# detailed split validation report
with open(R/'split_validation.md','w',encoding='utf-8') as f:
 f.write('# Split validation and leakage audit\n\n')
 f.write('## Quy tắc áp dụng\n\n')
 f.write('- Train: ngày đăng trước 2025-01-01 (2022–2024).\n- Validation: 2025-01-01 đến 2025-12-31.\n- Test: từ 2026-01-01 đến ngày cuối dữ liệu.\n- Nhãn mục tiêu mặc định: `topic_primary`, phải được hiểu là **weak labels** tự động, chưa phải nhãn vàng.\n- Đây là split mặc định được tạo để hoàn thiện bàn giao theo yêu cầu; nếu nhóm thay đổi nhãn hoặc mốc thời gian, cần tái sinh manifest.\n\n')
 f.write('## Kết quả kiểm tra\n\n')
 f.write(f"- CSV: {len(df):,} dòng; manifest: {len(manifest):,} dòng; tổng số dòng trong 3 split = {sum(split_counts.values()):,}.\n")
 for n in ['train','validation','test']:
  x=df[df.split==n]
  f.write(f"- **{n}**: {len(x):,} bài ({len(x)/len(df):.1%}), {x.publish_date.min().date()} đến {x.publish_date.max().date()}.\n")
 f.write(f"- ID trong manifest duy nhất: {checks['manifest_article_ids_unique']}. Không thiếu split: {checks['no_missing_split']}.\n")
 f.write(f"- Ứng viên trùng gần theo tiêu đề: {len(pairs_df):,} cặp; trong đó {checks['near_duplicate_candidates_cross_split']:,} cặp khác split. Xem `near_duplicate_title_candidates.csv`.\n\n")
 f.write(f"- Cụm trong metadata audit hiện đi qua nhiều split: **{checks['metadata_duplicate_clusters_cross_split']}** cụm. Đây là cảnh báo leakage cần xử lý trước khi đánh giá cuối; xem bảng dưới.\n\n")
 if cluster_cross_split:
  f.write('| Cụm | Số bài | Split | Article IDs |\n|---|---:|---|---|\n')
  for row in cluster_cross_split:
   f.write(f"| `{row['dup_cluster_id']}` | {row['article_count']} | {row['splits']} | {row['article_ids']} |\n")
  f.write('\n')
 f.write(f"- Để không dùng các bản ghi đã biết có rủi ro cross-split khi modeling, `modeling_eligibility_manifest.csv` chuyển **{checks['modeling_review_hold_rows']}** bản ghi liên quan sang `review_hold`; không xóa khỏi temporal manifest. Eligible counts: train {checks['modeling_eligible_split_counts']['train']:,}, validation {checks['modeling_eligible_split_counts']['validation']:,}, test {checks['modeling_eligible_split_counts']['test']:,}.\n\n")
 topic_table=pd.crosstab(df['topic_primary'],df['split']).reindex(columns=['train','validation','test'],fill_value=0)
 source_table=pd.crosstab(df['source_name'],df['split']).reindex(columns=['train','validation','test'],fill_value=0)
 f.write('### Phân bố nhãn weak theo split\n\n')
 f.write('| Topic primary (weak label) | Train | Validation | Test |\n|---|---:|---:|---:|\n')
 for label,row in topic_table.iterrows():
  f.write(f"| {label} | {int(row['train'])} | {int(row['validation'])} | {int(row['test'])} |\n")
 f.write('\n### Phân bố nguồn theo split\n\n')
 f.write('| Nguồn | Train | Validation | Test |\n|---|---:|---:|---:|\n')
 for label,row in source_table.iterrows():
  f.write(f"| {label} | {int(row['train'])} | {int(row['validation'])} | {int(row['test'])} |\n")
 f.write('\n')
 f.write('## Cảnh báo diễn giải\n\n')
 f.write('- Kiểm tra trùng gần chỉ là rà soát ứng viên theo tiêu đề với ngưỡng fuzzy ratio >= 90 trong các block tiêu đề; không phải kiểm định đầy đủ nội dung, không kết luận cặp nào chắc chắn trùng. Cần xem thủ công các cặp, đặc biệt cặp `cross_split=True`.\n')
 f.write('- `split_manifest.csv` giữ nguyên phân chia theo thời gian để audit. Khi modeling, dùng `modeling_eligibility_manifest.csv` và chỉ lấy `modeling_split` thuộc train/validation/test; các bản ghi thuộc candidate/cụm đã biết được giữ ở `review_hold`, không bị xóa. Rà soát thủ công trước khi đưa chúng trở lại.\n')
 f.write('- Rà soát tiêu đề theo block là heuristic không toàn diện; holdout này giảm rủi ro đã phát hiện nhưng không chứng minh không còn leakage.\n')
 f.write('- Chia theo thời gian mô phỏng dự đoán bài trong tương lai; phân bố chủ đề có thể lệch theo thời gian. Báo cáo macro-F1 và từng lớp, nhất là lớp hiếm.\n')
 f.write('- Khi `topic_primary` là target, tuyệt đối không đưa chính nó hoặc biến suy ra trực tiếp từ nó vào features. Không dùng `article_id`, `source_url`, `matched_keywords`, `topic_secondary`, `relevance_score`, `relevance_status`, `data_quality_note` hay `collection_date` làm feature mặc định.\n')
 f.write('- Không huấn luyện mô hình trong bước này. Các file split là manifest/metadata, không phải tập đặc trưng đã mã hóa.\n')
# Descriptive statistics and charts for the handoff; lengths are calculated from content, not raw word_count.
df['year_month']=df['publish_date'].dt.to_period('M').astype(str)
df['content_word_count_calculated']=df['content'].fillna('').astype(str).str.split().str.len()
stats={
 'rows':int(len(df)),
 'date_range':[df['publish_date'].min().strftime('%Y-%m-%d'),df['publish_date'].max().strftime('%Y-%m-%d')],
 'sources':df['source_name'].value_counts().to_dict(),
 'year_month':df['year_month'].value_counts().sort_index().to_dict(),
 'topics':df['topic_primary'].value_counts().to_dict(),
 'locations':df['location'].fillna('').replace('', '(trống)').value_counts().to_dict(),
 'content_word_count_calculated':{
     'mean':round(float(df['content_word_count_calculated'].mean()),2),
     'median':float(df['content_word_count_calculated'].median()),
     'min':int(df['content_word_count_calculated'].min()),
     'max':int(df['content_word_count_calculated'].max()),
     'p90':float(df['content_word_count_calculated'].quantile(.9)),
 },
}
def save_bar(series,title,ylabel,path,limit=None,rotate=45):
    values=series.head(limit) if limit else series
    fig,ax=plt.subplots(figsize=(12,6))
    values.plot(kind='bar',ax=ax,color='#4472C4')
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel('')
    ax.tick_params(axis='x',labelrotation=rotate)
    fig.tight_layout()
    fig.savefig(CHARTS/path,dpi=150)
    plt.close(fig)
save_bar(df['source_name'].value_counts(),'Articles by source','Articles','articles_by_source.png',rotate=30)
save_bar(df['year_month'].value_counts().sort_index(),'Articles by year-month','Articles','articles_by_year_month.png',rotate=60)
save_bar(df['topic_primary'].value_counts(),'Articles by primary weak label','Articles','articles_by_topic.png',rotate=30)
save_bar(df['location'].fillna('').replace('','(trống)').value_counts(),'Top 15 locations','Articles','articles_by_location.png',limit=15,rotate=45)
fig,ax=plt.subplots(figsize=(10,6))
ax.hist(df['content_word_count_calculated'],bins=40,color='#70AD47')
ax.set_title('Calculated article body length distribution')
ax.set_xlabel('Whitespace-separated words in content')
ax.set_ylabel('Articles')
fig.tight_layout()
fig.savefig(CHARTS/'content_word_count_distribution.png',dpi=150)
plt.close(fig)
with open(R/'process_statistics.md','w',encoding='utf-8') as f:
    f.write('# Process dataset statistics\n\n')
    f.write(f"- Records: {stats['rows']:,}\n- Date range: {stats['date_range'][0]} to {stats['date_range'][1]}\n")
    f.write('- `topic_primary` is an automatically generated weak label, not verified ground truth.\n')
    f.write('- Text length is recalculated as whitespace-separated tokens in `content`; it is not the raw `word_count` field and does not imply linguistic tokenization.\n\n')
    for title,key in [('Articles by source','sources'),('Articles by year-month','year_month'),('Primary weak labels','topics'),('Locations','locations')]:
        f.write(f'## {title}\n\n| Category | Articles |\n|---|---:|\n')
        for category,count in stats[key].items():
            f.write(f'| {category} | {count:,} |\n')
        f.write('\n')
    f.write('## Content length\n\n')
    f.write(f"- Mean: {stats['content_word_count_calculated']['mean']:,} words\n")
    f.write(f"- Median: {stats['content_word_count_calculated']['median']:,} words\n")
    f.write(f"- Minimum / maximum: {stats['content_word_count_calculated']['min']:,} / {stats['content_word_count_calculated']['max']:,}\n")
    f.write(f"- 90th percentile: {stats['content_word_count_calculated']['p90']:,} words\n\n")
    f.write('## Charts\n\n')
    for filename in ['articles_by_source.png','articles_by_year_month.png','articles_by_topic.png','articles_by_location.png','content_word_count_distribution.png']:
        f.write(f'- `charts/{filename}`\n')
    f.write('\n## Split notes\n\n')
    f.write(f"- Train: {checks['split_counts']['train']:,}; validation: {checks['split_counts']['validation']:,}; test: {checks['split_counts']['test']:,}.\n")
    f.write(f"- Title candidate pairs: {checks['near_duplicate_candidate_pairs']:,}, including {checks['near_duplicate_candidates_cross_split']:,} across splits. These are screening candidates, not confirmed duplicates.\n")
    f.write(f"- Metadata duplicate clusters spanning splits: {checks['metadata_duplicate_clusters_cross_split']}; review `split_validation.md` before final evaluation.\n")
hp=R/'handoff_to_modeling.md'
with open(hp,'w',encoding='utf-8') as f:
 f.write('# Bàn giao cho nhóm Modeling\n\n## Trạng thái\n\n')
 f.write('- Đã sinh manifest theo thời gian: train trước 2025-01-01, validation trong năm 2025, test từ 2026-01-01.\n')
 f.write(f"- Quy mô: train {checks['split_counts']['train']:,}, validation {checks['split_counts']['validation']:,}, test {checks['split_counts']['test']:,}; tổng {len(df):,} bài.\n")
 f.write('- `topic_primary` chỉ là **weak label** tự động, không phải nhãn vàng. Cần xác nhận đây là nhãn mục tiêu trước khi huấn luyện; 56 mẫu review thủ công hiện vẫn chờ con người xác nhận.\n')
 f.write('- Đây là manifest metadata, không phải feature matrix. Chưa huấn luyện mô hình.\n\n')
 f.write('## Việc bắt buộc trước khi báo cáo kết quả cuối\n\n')
 f.write(f"- Rà soát thủ công {checks['near_duplicate_candidates_cross_split']:,} cặp tiêu đề ứng viên đi qua split và {checks['metadata_duplicate_clusters_cross_split']} cụm duplicate metadata đi qua split. Báo cáo audit ghi IDs/splits; không tự động loại hoặc chuyển bài.\n")
 f.write('- Xác nhận nhãn đích, định nghĩa task và tiêu chí đánh giá; loại `article_id`, nhãn mục tiêu và mọi trường suy ra trực tiếp từ nhãn khỏi features.\n')
 f.write('- Chỉ sau khi rà soát leakage và quyết định xử lý được ghi nhận, mới cố định split dùng cho đánh giá cuối. Nếu thay đổi dữ liệu hoặc quy tắc, chạy lại script sinh audit.\n')
 f.write('- Với phân chia theo thời gian, báo cáo macro-F1 và chỉ số từng lớp; nêu rõ mất cân bằng và tính yếu của nhãn.\n\n')
 f.write('## File đầu ra\n\n')
 f.write('- `5_process/splits/split_manifest.csv` và `train_manifest.csv`, `validation_manifest.csv`, `test_manifest.csv`.\n')
 f.write('- `5_process/splits/modeling_eligibility_manifest.csv`: giữ toàn bộ ID; các ứng viên/cụm đã biết giao split được gắn `modeling_split=review_hold`, không dùng cho đánh giá đến khi review.\n')
 f.write('- `5_process/reports/split_validation.md`: quy tắc, số lượng, phân bố và cảnh báo.\n')
 f.write('- `5_process/reports/split_and_leakage_checks.json`: kiểm tra dạng máy đọc được.\n')
 f.write('- `5_process/reports/near_duplicate_title_candidates.csv`: cặp tiêu đề cần review; là sàng lọc ứng viên, không xác nhận trùng.\n')
(S/'README.md').write_text('''# Split manifests (proposed default)\n\nThese files contain split assignments and audit metadata, not model-ready features. `topic_primary` is an automatically generated **weak label**, not gold truth.\n\n- `train_manifest.csv`: `publish_date` < 2025-01-01\n- `validation_manifest.csv`: calendar year 2025\n- `test_manifest.csv`: 2026-01-01 onward\n- `split_manifest.csv`: all records with split assignment\n\n`article_id` is included only as a row key for audit/rejoining; exclude it and the target label from model features. Review `../reports/near_duplicate_title_candidates.csv`, especially `cross_split=True`, and the duplicate-cluster warnings in `../reports/split_validation.md` before final evaluation. Re-run the audit script after changing the source data or split policy. No model training was performed.\n''',encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False,indent=2))
