import streamlit as st
import datetime
import isodate
from googleapiclient.discovery import build

# === 网页配置 ===
st.set_page_config(page_title="🔥 油管爆款雷达", layout="wide")

# === 标题和简介 ===
st.title("🔥 YouTube Shorts 爆款雷达")
st.markdown("输入关键词，寻找过去 48 小时内 **每小时播放量 (VPH)** 最高的视频。")

# === 侧边栏：设置 ===
with st.sidebar:
    st.header("⚙️ 设置")
    api_key = st.text_input("输入 YouTube API Key", type="password")
    st.info("提示：API Key 仅在本次会话使用，不会被永久保存。")

# === 主界面：搜索 ===
col1, col2 = st.columns([3, 1])
with col1:
    keyword = st.text_input("输入关键词 (例如: AI Story, Scary facts)", "AI Story #shorts")
with col2:
    search_btn = st.button("🔍 开始搜索", use_container_width=True)

# === 核心逻辑 ===
def get_viral_videos(api_key, query):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # 时间设定：48小时内
        time_window = datetime.datetime.utcnow() - datetime.timedelta(hours=48)
        published_after = time_window.isoformat("T") + "Z"

        # 1. 搜索
        search_response = youtube.search().list(
            q=query, part='id', maxResults=50, order='viewCount',
            type='video', publishedAfter=published_after, videoDuration='short'
        ).execute()

        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

        if not video_ids:
            return []

        # 2. 获取详情
        stats_response = youtube.videos().list(
            id=','.join(video_ids), part='snippet,statistics'
        ).execute()

        results = []
        for item in stats_response['items']:
            stats = item['statistics']
            snippet = item['snippet']
            view_count = int(stats.get('viewCount', 0))

            # 过滤低播放
            if view_count < 500: continue

            publish_time = isodate.parse_datetime(snippet['publishedAt'])
            hours_ago = (datetime.datetime.utcnow() - publish_time.replace(tzinfo=None)).total_seconds() / 3600
            if hours_ago < 0.1: hours_ago = 0.1

            vph = int(view_count / hours_ago)
            
            # 获取最高清封面
            thumbs = snippet['thumbnails']
            thumb_url = thumbs.get('high', thumbs.get('medium', thumbs.get('default')))['url']

            results.append({
                'title': snippet['title'],
                'vph': vph,
                'views': view_count,
                'hours': round(hours_ago, 1),
                'channel': snippet['channelTitle'],
                'url': f"https://www.youtube.com/shorts/{item['id']}",
                'thumb': thumb_url
            })
        
        # 排序
        results.sort(key=lambda x: x['vph'], reverse=True)
        return results

    except Exception as e:
        st.error(f"发生错误: {e}")
        return []

# === 执行搜索 ===
if search_btn:
    if not api_key:
        st.warning("⚠️ 请先在左侧侧边栏输入 API Key！")
    else:
        with st.spinner('正在全网扫描爆款，请稍候...'):
            videos = get_viral_videos(api_key, keyword)
            
            if videos:
                st.success(f"成功找到 {len(videos)} 个视频！")
                
                # 展示结果
                for v in videos:
                    # 使用卡片式布局
                    with st.container():
                        c1, c2 = st.columns([1, 3])
                        
                        # 左列：封面
                        with c1:
                            st.image(v['thumb'], use_container_width=True)
                        
                        # 右列：信息
                        with c2:
                            st.subheader(f"[{v['title']}]({v['url']})") # 标题带链接
                            st.caption(f"频道: {v['channel']} | 发布于 {v['hours']} 小时前")
                            
                            # 数据指标
                            m1, m2 = st.columns(2)
                            m1.metric("🔥 VPH (热度)", v['vph'])
                            m2.metric("👁️ 总播放", v['views'])
                            
                        st.divider() # 分割线
            else:
                st.warning("未找到符合条件的视频，请换个关键词试试。")