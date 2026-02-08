import streamlit as st
import datetime
import isodate
from googleapiclient.discovery import build

# === 1. 页面全局配置 (必须在第一行) ===
st.set_page_config(
    page_title="ViralRadar Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 2. 自定义 CSS (打造高端感) ===
# 这一段 CSS 会隐藏掉 Streamlit 默认的红线和脚标，并调整字体
st.markdown("""
    <style>
        /* 隐藏顶部默认装饰条 */
        header {visibility: hidden;}
        /* 隐藏底部 Footer */
        footer {visibility: hidden;}
        
        /* 调整主标题样式 */
        .main-title {
            font-size: 3rem !important;
            font-weight: 800;
            color: #FF4B4B; 
            text-align: center;
            margin-bottom: 10px;
        }
        .sub-title {
            font-size: 1.2rem;
            color: #888;
            text-align: center;
            margin-bottom: 40px;
        }
        
        /* 卡片悬停效果 (仅装饰) */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            transition: all 0.3s ease;
        }
    </style>
""", unsafe_allow_html=True)

# === 3. 核心逻辑函数 ===
@st.cache_data(ttl=600) # 添加缓存，防止重复请求浪费配额
def search_videos(api_key, query, hours_filter):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 动态计算时间窗口
        time_window = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_filter)
        published_after = time_window.isoformat("T") + "Z"

        # 1. 搜索 API
        search_response = youtube.search().list(
            q=query, part='id', maxResults=50, order='viewCount',
            type='video', publishedAfter=published_after, videoDuration='short'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            return []

        # 2. 详情 API
        stats_response = youtube.videos().list(
            id=','.join(video_ids), part='snippet,statistics'
        ).execute()

        results = []
        for item in stats_response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            view_count = int(stats.get('viewCount', 0))

            # 过滤超低播放量
            if view_count < 200: continue

            publish_time = isodate.parse_datetime(snippet['publishedAt'])
            hours_ago = (datetime.datetime.utcnow() - publish_time.replace(tzinfo=None)).total_seconds() / 3600
            if hours_ago < 0.1: hours_ago = 0.1

            vph = int(view_count / hours_ago)
            
            # 获取最高清封面
            thumbs = snippet['thumbnails']
            thumb_url = thumbs.get('maxres', thumbs.get('high', thumbs.get('medium')))['url']

            results.append({
                'title': snippet['title'],
                'vph': vph,
                'views': view_count,
                'hours': round(hours_ago, 1),
                'channel': snippet['channelTitle'],
                'url': f"https://www.youtube.com/shorts/{item['id']}",
                'thumb': thumb_url,
                'date': publish_time.strftime("%Y-%m-%d")
            })
        
        # 按 VPH 排序
        results.sort(key=lambda x: x['vph'], reverse=True)
        return results

    except Exception as e:
        st.error(f"API 连接错误: {str(e)}")
        return []

# === 4. 侧边栏设计 (控制台) ===
with st.sidebar:
    st.markdown("### ⚡ 控制台 Control Panel")
    
    # API Key 输入
    api_key = st.text_input("YouTube API Key", type="password", help="您的 API 密钥")
    
    st.markdown("---")
    
    # 时间筛选器 (User Request)
    st.markdown("#### ⏳ 时间范围 Time Range")
    time_option = st.selectbox(
        "选择抓取范围",
        ("24小时 (最新爆发)", "72小时 (稳定热门)", "一周 (长期趋势)", "一月 (月度爆款)"),
        index=0 # 默认选第一个
    )
    
    # 将选项映射为小时数
    hours_map = {
        "24小时 (最新爆发)": 24,
        "72小时 (稳定热门)": 72,
        "一周 (长期趋势)": 168,
        "一月 (月度爆款)": 720
    }
    selected_hours = hours_map[time_option]
    
    st.markdown("---")
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.8em;'>当前模式: {time_option}</div>", unsafe_allow_html=True)


# === 5. 主界面设计 ===

# 标题区
st.markdown('<div class="main-title">⚡ VIRAL RADAR PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">发现 YouTube Shorts 流量密码 | 全球爆款雷达</div>', unsafe_allow_html=True)

# 搜索区 (居中布局)
col_spacer1, col_input, col_btn, col_spacer2 = st.columns([1, 4, 1, 1])

with col_input:
    keyword = st.text_input("", placeholder="输入关键词，例如: AI Story, Scary facts...", label_visibility="collapsed")

with col_btn:
    start_search = st.button("🚀 开始扫描", use_container_width=True, type="primary")

st.divider()

# === 6. 结果展示 (卡片流布局) ===
if start_search:
    if not api_key:
        st.toast("⚠️ 请先在左侧侧边栏设置 API Key", icon="🔒")
    elif not keyword:
        st.toast("⚠️ 请输入搜索关键词", icon="🔍")
    else:
        with st.spinner(f"正在扫描过去 {selected_hours} 小时内的数据..."):
            videos = search_videos(api_key, keyword, selected_hours)
            
            if videos:
                st.success(f"🎯 扫描完成！发现 {len(videos)} 个潜在爆款")
                
                # === 网格布局逻辑 ===
                # 每行显示 4 个视频，看起来更像 Youtube
                COLS_PER_ROW = 4
                rows = [videos[i:i + COLS_PER_ROW] for i in range(0, len(videos), COLS_PER_ROW)]

                for row in rows:
                    cols = st.columns(COLS_PER_ROW)
                    for idx, v in enumerate(row):
                        with cols[idx]:
                            # 使用 container 创建带边框的卡片效果
                            with st.container(border=True):
                                # 1. 封面图
                                st.image(v['thumb'], use_container_width=True)
                                
                                # 2. 核心指标 (VPH) - 使用 Metric 组件显得很专业
                                delta_color = "normal" if v['vph'] < 1000 else "inverse" # 爆款反色显示
                                st.metric(
                                    label="🔥 热度 (VPH)", 
                                    value=f"{v['vph']}", 
                                    delta="极速飙升" if v['vph'] > 2000 else None
                                )
                                
                                # 3. 标题和链接
                                st.markdown(f"**[{v['title']}]({v['url']})**")
                                
                                # 4. 辅助信息
                                st.caption(f"📺 {v['channel']}")
                                st.caption(f"👁️ 总播放: {v['views']/1000:.1f}k • 🕒 {v['hours']}h前")
                                
            else:
                st.warning("⚠️ 该时间段内未找到相关爆款，尝试放宽时间范围或更换关键词。")
