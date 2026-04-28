import streamlit as st
from st_supabase_connection import SupabaseConnection
import re
import requests
from datetime import datetime

# --- 1. 基础配置与高级 UI 样式 ---
st.set_page_config(page_title="Music 30 Days", layout="wide", page_icon="🎧")

# 注入自定义 CSS
st.markdown("""
    <style>
    /* 整体背景与宽度限制 */
    .stApp { max-width: 900px; margin: 0 auto; }
    
    /* 现代感音乐卡片 */
    .music-card-header {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem;
        border-radius: 15px 15px 0 0;
        border: 1px solid #374151;
        border-bottom: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .music-card-body {
        background: #161b22;
        padding: 1.2rem;
        border-radius: 0 0 15px 15px;
        border: 1px solid #30363d;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .user-badge {
        color: #58a6ff;
        font-weight: 700;
        font-size: 1.1rem;
    }
    
    .day-badge {
        background: #238636;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    
    /* 交互动效 */
    .stButton>button:hover { transform: scale(1.02); transition: 0.2s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 挑战主题与权限读取 ---
DEFAULT_CHALLENGES = [
    "歌名里带有颜色的歌", "歌名里带有数字的歌", "让你想起夏天的歌", "让你想起宁愿忘记的人的歌", 
    "需要调大音量放的歌", "让你想尽情跳舞的歌", "适合开车时听的歌", "关于药物或酒精的歌", 
    "能让你感到开心的歌", "能让你感到悲伤的歌", "永远不会厌倦的歌", "来自你青春期前(13岁)的歌", 
    "你喜欢的来自70年代的歌", "你想在婚礼上播的歌", "你喜欢的由别的艺术家翻唱的歌", "你的挚爱经典",
    "你会和某个人在KTV唱的二重唱", "发行于你出生那年的歌", "使你开始思考生活的歌", "对于你有很多意义的歌", 
    "带有某人名字在你歌名中你喜欢的歌", "激励你上进的歌", "你觉得每个人都要听的歌", "来自你遗憾解散的乐队的歌", 
    "你喜欢的一个已经逝去艺术家的歌", "让你想要陷入爱情的歌", "让你心碎的歌", "来自一位你超喜欢Ta声音的艺术家的歌",
    "一首在你童年记忆里的歌", "一首让你想起自己的歌"
]

# 从 Secrets 安全读取管理员名称，如果没设则默认为空字符串
ADMIN_NAME = st.secrets.get("ADMIN_USER", "")

# --- 3. 核心解析逻辑 ---
def get_player_html(url):
    if not url or str(url) == "nan": return None
    url = str(url).strip()
    
    if "163cn.tv" in url:
        try:
            res = requests.get(url, allow_redirects=True, timeout=5)
            url = res.url
        except: pass

    if "music.apple.com" in url:
        clean_url = url.split('?')[0]
        embed_url = clean_url.replace("music.apple.com", "embed.music.apple.com")
        return f'<iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="175" style="width:100%;max-width:660px;overflow:hidden;background:transparent;border-radius:12px;" src="{embed_url}"></iframe>'
    
    if "163.com" in url:
        sid = re.search(r'id=(\d+)', url)
        if sid:
            # 增加网易云高度解决控件遮挡
            return f'<iframe frameborder="no" border="0" marginwidth="0" marginheight="0" width=330 height=110 src="//music.163.com/outchain/player?type=2&id={sid.group(1)}&auto=0&height=90"></iframe>'
    return None

# --- 4. 侧边栏 ---
conn = st.connection("supabase", type=SupabaseConnection)

with st.sidebar:
    st.title("🎧 控制中心")
    if 'user' in st.session_state:
        st.write(f"你好, **{st.session_state.user}**")
        if st.session_state.user == ADMIN_NAME:
            st.info("🛡️ 已识别管理员权限")
        
        with st.expander("📝 自定义挑战主题"):
            st.caption("修改后仅对当前访问有效，永久修改请编辑代码")
            custom_input = st.text_area("30天列表:", value="\n".join(DEFAULT_CHALLENGES), height=250)
            CHALLENGES = custom_input.split("\n")
        
        if st.button("注销登录"):
            del st.session_state.user
            st.rerun()
    else:
        st.caption("请输入昵称参与挑战")

# --- 5. 主逻辑 ---
if 'user' not in st.session_state:
    st.title("🎵 30天推歌挑战")
    u = st.text_input("你的名字:", placeholder="输入昵称...")
    if st.button("开启音乐日记"):
        if u.strip():
            st.session_state.user = u.strip()
            st.rerun()
else:
    tab1, tab2 = st.tabs(["✨ 新增打卡", "🌌 朋友圈"])

    with tab1:
        selected_day = st.slider("今天是第几天？", 1, 30, 1)
        st.markdown(f"#### Day {selected_day}: {DEFAULT_CHALLENGES[selected_day-1]}")
        
        with st.form("post_form", clear_on_submit=True):
            m_url = st.text_input("粘贴歌曲链接 (网易云/AM)")
            m_note = st.text_area("写点什么...")
            if st.form_submit_button("发送到云端"):
                if m_url:
                    conn.table("music_challenge").upsert({
                        "day": selected_day, 
                        "url": m_url, 
                        "comment": m_note, 
                        "user_name": st.session_state.user
                    }).execute()
                    st.toast("发布成功!", icon="🎉")
                    st.rerun()

    with tab2:
        try:
            res = conn.table("music_challenge").select("*").order("created_at", desc=True).execute()
            for row in res.data:
                # 渲染视觉卡片头部
                st.markdown(f"""
                <div class="music-card-header">
                    <span class="user-badge">👤 {row['user_name']}</span>
                    <span class="day-badge">Day {row['day']}</span>
                </div>
                <div class="music-card-body">
                    <p style="color:#8b949e; font-size:0.9rem; margin-bottom:15px;">主题：{DEFAULT_CHALLENGES[int(row['day'])-1]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 播放器与内容
                c1, c2 = st.columns([4, 1])
                with c1:
                    player = get_player_html(row['url'])
                    if player:
                        st.components.v1.html(player, height=180 if "apple" in str(row['url']) else 120)
                    else:
                        st.link_button("🔗 跳转听歌", row['url'])
                    
                    if row['comment']:
                        st.chat_message("user").write(row['comment'])
                
                with c2:
                    # 管理员删除逻辑：Secrets 中的管理员或发布者本人
                    if st.session_state.user == ADMIN_NAME or row['user_name'] == st.session_state.user:
                        if st.button("🗑️", key=f"del_{row['id']}", help="删除此记录"):
                            conn.table("music_challenge").delete().eq("id", row['id']).execute()
                            st.rerun()
                st.divider()
        except Exception as e:
            st.error(f"加载动态失败: {e}")