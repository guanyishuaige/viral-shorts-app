import streamlit as st
import datetime
import isodate
from googleapiclient.discovery import build

# ==========================================
# 1. 配置与语言包 (Configuration & i18n)
# ==========================================

st.set_page_config(
    page_title="ViralRadar Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 语言字典
TRANSLATIONS = {
    "中文": {
        "sidebar_title": "趋势工作台",
        "sidebar_dashboard": "实时趋势",
        "sidebar_category": "分类筛选",
        "sidebar_fav": "收藏夹",
        "search_placeholder": "搜索关键词 (例如: AI Story, Minecraft)...",
        "search_btn": "一键刷新",
        "last_updated": "上次更新: 刚刚",
        "filter_all": "全部",
        "filter_hot": "热门爆款",
        "filter_growth": "高潜力",
        "card_views": "播放",
        "card_time": "前",
        "card_heat": "爆款指数",
        "card_analyze": "深度分析",
        "detail_back": "返回列表",
        "detail_reason": "AI 爆款原因推测",
        "detail_script": "脚本结构分析",
        "detail_audience": "受众画像",
        "loading": "正在全网扫描数据..."
    },
    "English": {
        "sidebar_title": "Trend Workbench",
        "sidebar_dashboard": "Dashboard",
        "sidebar_category": "Categories",
        "sidebar_fav": "Favorites",
        "search_placeholder": "Search keywords (e.g., AI Story)...",
        "search_btn": "Quick Scan",
        "last_updated": "Updated: Just now",
        "filter_all": "All",
        "filter_hot": "Hot & Viral",
        "filter_growth": "High Growth",
        "card_views": "Views",
        "card_time": "ago",
        "card_heat": "Heat Score",
        "card_analyze": "Analyze",
        "detail_back": "Back to List",
        "detail_reason": "AI Viral Reason",
        "detail_script": "Script Analysis",
        "detail_audience": "Audience Persona",
        "loading": "Scanning for viral content..."
    }
}

# ==========================================
# 2. 深度定制 CSS (核心美化)
# ==========================================
# 提取自你提供的 HTML 文件颜色：
# 背景: #101623, 卡片: #1c2536, 蓝色主色: #0d59f2, 绿色: #22c55e

st.markdown("""
    <style>
        /* 全局背景色 */
        .stApp {
            background-color: #101623;
            color: #ffffff;
        }
        
        /* 侧边栏背景 */
        section[data-testid="stSidebar"] {
            background-color: #0b0f19;
            border-right: 1px solid #1c2536;
        }
        
        /* 隐藏顶部红线和菜单 */
        header {visibility: hidden;}
        
        /* 输入框美化 */
        .stTextInput input {
            background-color: #1c2536 !important;
            color: white !important;
            border: 1px solid #2d3748 !important;
            border-radius: 8px !important;
        }
        
        /* 按钮美化 (蓝色主色) */
        .stButton button {
            background-color: #0d59f2 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            box-shadow: 0 4px 14px 0 rgba(13, 89, 242, 0.39);
            transform: translateY(-1px);
        }

        /* 卡片容器样式 (模拟 CSS Grid) */
        .video-card {
            background-color: #1c2536;
            border: 1px solid #2d3748;
            border-radius: 12px;
            padding: 0;
            overflow: hidden;
            transition: transform 0.2s;
            margin-bottom: 20px;
        }
        .video-card:hover {
            border-color: #0d59f2;
            transform: translateY(-2px);
        }
        
        /* 详情页样式 */
        .detail-box {
            background-color: #1c2536;
            border: 1px solid #2d3748;
            border-radius: 12px;
            padding: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 核心逻辑 (后端)
# ==========================================

if 'current_view' not in st.session_state:
    st.session_state.current_view = 'dashboard'
if 'selected_video' not in st.session_state:
    st.session_state.selected_video = None

@st.cache_data(ttl=600)
def search_videos(api_key, query):
    if not api_key: return []
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        time_window = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
        published_after = time_window.isoformat("T") + "Z"

        search_response = youtube.search().list(
            q=query, part='id', maxResults=12, order='viewCount', # 限制数量以适应布局
            type='video', publishedAfter=published_after, videoDuration='short'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        if not video_ids: return []

        stats_response = youtube.videos().list(
            id=','.join(video_ids), part='snippet,statistics'
        ).execute()

        results = []
        for item in stats_response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            view_count = int(stats.get('viewCount', 0))
            if view_count < 500: continue
            
            # 计算发布时间
            publish_time = isodate.parse_datetime(snippet['publishedAt'])
            hours_ago = (datetime.datetime.utcnow() - publish_time.replace(tzinfo=None)).total_seconds() / 3600
            
            # 封面图
            thumbs = snippet['thumbnails']
            thumb_url = thumbs.get('maxres', thumbs.get('high', thumbs.get('medium')))['url']
            
            # 爆款指数
            vph = int(view_count / (hours_ago if hours_ago > 0.1 else 0.1))

            results.append({
                'id': item['id'],
                'title': snippet['title'],
                'vph': vph,
                'views': view_count,
                'hours': round(hours_ago, 1),
                'channel': snippet['channelTitle'],
                'thumb': thumb_url,
                'desc': snippet.get('description', ''),
                'url': f"https://www.youtube.com/shorts/{item['id']}"
            })
        
        results.sort(key=lambda x: x['vph'], reverse=True)
        return results

    except Exception as e:
        st.error(f"Error: {e}")
        return []

# ==========================================
# 4. 界面构建 (前端)
# ==========================================

# --- 侧边栏 ---
with st.sidebar:
    # 语言切换
    lang_code = st.selectbox("🌐 Language / 语言", ["中文", "English"])
    t = TRANSLATIONS[lang_code] # 获取当前语言包

    st.markdown(f"## ⚡ {t['sidebar_title']}")
    
    # API Key 输入 (带密码遮挡)
    api_key = st.text_input("API Key", type="password")
    
    st.markdown("---")
    
    # 模拟菜单 (高亮 dashboard)
    st.markdown(f"""
    <div style="background-color: #0d59f2; padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 5px;">
        🔥 {t['sidebar_dashboard']}
    </div>
    <div style="padding: 10px; color: #94a3b8;">📂 {t['sidebar_category']}</div>
    <div style="padding: 10px; color: #94a3b8;">❤️ {t['sidebar_fav']} <span style="float:right; background:#2d3748; padding:0 5px; border-radius:4px; font-size:0.8em">12</span></div>
    """, unsafe_allow_html=True)

# --- 主界面逻辑 ---

# 1. 如果在详情页视图
if st.session_state.current_view == 'detail' and st.session_state.selected_video:
    v = st.session_state.selected_video
    
    # 顶部导航
    if st.button(f"← {t['detail_back']}"):
        st.session_state.current_view = 'dashboard'
        st.rerun()
        
    st.markdown(f"### {v['title']}")
    
    # 详情页布局 (参考你的 video_deep_analysis_detail_page.html)
    c1, c2 = st.columns([1, 2])
    
    with c1:
        # 左侧：视频播放器模拟
        st.image(v['thumb'], use_container_width=True)
        # 数据卡片
        m1, m2 = st.columns(2)
        m1.metric("Total Views", f"{v['views']/1000:.1f}k", "+12.5%")
        m2.metric("VPH (Heat)", v['vph'], "High Potential")
        
        st.info("💡 Pro Tip: 点击上方图片可跳转到 YouTube 观看原视频")

    with c2:
        # 右侧：AI 分析 (模拟你的 HTML 右侧)
        st.markdown(f"""
        <div class="detail-box" style="border-left: 4px solid #0d59f2; margin-bottom: 20px;">
            <h4 style="margin-top:0;">🤖 {t['detail_reason']}</h4>
            <p style="color: #cbd5e1;">
                该视频在前 <b>3秒</b> 提出了强烈的视觉钩子（Hook）。
                结合 <b>{v['channel']}</b> 的一贯风格，这种叙事结构非常适合 Shorts 算法推荐。
                播放量每小时增长 <b>{v['vph']}</b>，属于 <b>S+级</b> 爆款。
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 脚本与受众 Tab
        tab1, tab2 = st.tabs([f"📝 {t['detail_script']}", f"👥 {t['detail_audience']}"])
        with tab1:
            st.markdown(f"""
            - **0-3s (Hook)**: 快速剪辑，提出痛点。
            - **3-15s (Body)**: 展示核心内容，节奏紧凑。
            - **15s+ (CTA)**: 引导评论和关注。
            """)
        with tab2:
            st.markdown("主要受众群体：**18-35岁**，对科技/娱乐感兴趣的男性用户。")

# 2. 如果在仪表盘视图 (默认)
else:
    # --- 顶部搜索栏 ---
    c_search, c_btn = st.columns([4, 1])
    with c_search:
        query = st.text_input("", placeholder=t['search_placeholder'], label_visibility="collapsed")
    with c_btn:
        do_search = st.button(f"⚡ {t['search_btn']}", use_container_width=True)
    
    # --- 标签栏 (Filters) ---
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 20px; overflow-x: auto;">
        <span style="background:#0d59f2; padding:5px 15px; border-radius:20px; font-size:0.9em; font-weight:bold;">{t['filter_all']}</span>
        <span style="background:#1c2536; border:1px solid #2d3748; padding:5px 15px; border-radius:20px; font-size:0.9em; color:#cbd5e1;">🔥 {t['filter_hot']}</span>
        <span style="background:#1c2536; border:1px solid #2d3748; padding:5px 15px; border-radius:20px; font-size:0.9em; color:#cbd5e1;">📈 {t['filter_growth']}</span>
    </div>
    """, unsafe_allow_html=True)

    # --- 搜索结果 ---
    if do_search and api_key and query:
        with st.spinner(t['loading']):
            results = search_videos(api_key, query)
            
            if not results:
                st.warning("未找到视频，请检查 API Key 或更换关键词。")
            else:
                # 瀑布流布局 (每行 4 个)
                cols = st.columns(4)
                for idx, video in enumerate(results):
                    with cols[idx % 4]:
                        # 渲染卡片 HTML
                        # 注意：这里我们用 HTML 渲染外观，用 Streamlit button 做交互
                        st.markdown(f"""
                        <div class="video-card">
                            <div style="position: relative; aspect-ratio: 9/16;">
                                <img src="{video['thumb']}" style="width:100%; height:100%; object-fit: cover;">
                                <div style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                                    🕒 {video['hours']}h {t['card_time']}
                                </div>
                                <div style="position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); padding: 10px;">
                                    <div style="color: white; font-weight: bold;">👁️ {video['views']/1000:.1f}k</div>
                                </div>
                            </div>
                            <div style="padding: 12px;">
                                <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                                    {video['title']}
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                                    <div style="font-size: 12px; color: #94a3b8;">{video['channel']}</div>
                                    <div style="background: rgba(13, 89, 242, 0.2); color: #3b82f6; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                                        🔥 {video['vph']}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 交互按钮 (放在卡片下方)
                        if st.button(f"🔍 {t['card_analyze']}", key=f"btn_{video['id']}"):
                            st.session_state.selected_video = video
                            st.session_state.current_view = 'detail'
                            st.rerun()

    elif not api_key:
        st.info("👋 请在左侧侧边栏输入您的 YouTube API Key 开始使用。")
    elif not query:
        st.info("👈 输入关键词开始挖掘爆款。")
