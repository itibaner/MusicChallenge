import streamlit as st
from st_supabase_connection import SupabaseConnection
import re
import requests
from datetime import datetime

# --- 1. 高级 UI 配置与全能 CSS ---
st.set_page_config(page_title="Music 30 Days", layout="wide", page_icon="🎧")

# 自定义 CSS 提升设计感 (黑色极简风)
st.markdown("""
    <style>
    /* 全局样式 */
    .stApp { max-width: 1000px; margin: 0 auto; background-color: #0e1117; }
    
    /* 登录界面微调 */
    .login-container { display: flex; justify-content: center; align-items: center; height: 70vh; }
    
    /* 朋友圈动态卡片 */
    .music-card {
        background-color: #161b22;
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid #30363d;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    .music-card:hover { transform: translateY(-3px); border-color: #58a6ff; }
    
    /* 管理员卡片高亮 (金边) */
    .admin-card { border-color: #f1c40f !important; border-width: 2px !important; box-shadow: 0 4px 15px rgba(241,196,15,0.3) !important; }
    
    /* 卡片内部元素 */
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    .user-name { color: #58a6ff; font-weight: 700; font-size: 1.2rem; }
    .day-badge { background-color: #238636; color: white; padding: 3px 12px; border-radius: 12px; font-size: 0.8rem; }
    .topic-line { color: #8b949e; font-size: 0.95rem; margin-bottom: 20px; font-style: italic; }
    .comment-area { margin-top: 15px; color: #d1d5da; font-size: 1rem; border-left: 3px solid #30363d; padding-left: 10px; }
    
    /* 交互动效 */
    .stButton>button:hover { transform: scale(1.03); transition: 0.2s; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 挑战主题与管理员权限 ---
# 30天挑战列表
CHALLENGES = [
    "歌名里带有颜色的歌", "歌名里带有数字的歌", "让你想起夏天的歌", "让你想起宁愿忘记的人的歌", 
    "需要调大音量放的歌", "让你想尽情跳舞的歌", "适合开车时听的歌", "关于药物或酒精的歌", 
    "能让你感到开心的歌", "能让你感到悲伤的歌", "永远不会厌倦的歌", "来自你青春期前(13岁)的歌", 
    "你喜欢的来自70年代的歌", "你想在婚礼上播的歌", "你喜欢的由别的艺术家翻唱的歌", "你的挚爱经典",
    "你会和某个人在KTV唱的二重唱", "发行于你出生那年的歌", "使你开始思考生活的歌", "对于你有很多意义的歌", 
    "带有某人名字在你歌名中你喜欢的歌", "激励你上进的歌", "你觉得每个人都要听的歌", "来自你遗憾解散的乐队的歌", 
    "你喜欢的一个已经逝去艺术家的歌", "让你想要陷入爱情的歌", "让你心碎的歌", "来自一位你超喜欢Ta声音的艺术家的歌",
    "一首在你童年记忆里的歌", "一首让你想起自己的歌"
]

# 从 Secrets 安全读取管理员名称
ADMIN_USER_NAME = st.secrets.get("ADMIN_USER", "")

# --- 3. 核心连接与解析逻辑 ---
# 建立 Supabase 连接
conn = st.connection("supabase", type=SupabaseConnection)

# 解析播放器 (Apple Music & 网易云短链接还原)
def get_player_html(url):
    if not url or str(url) == "nan": return None
    url = str(url).strip()
    
    # 1. 处理网易云短链接 (163cn.tv)
    if "163cn.tv" in url:
        try:
            res = requests.get(url, allow_redirects=True, timeout=5)
            url = res.url
        except: pass

    # 2. Apple Music
    if "music.apple.com" in url:
        clean_url = url.split('?')[0]
        embed_url = clean_url.replace("music.apple.com", "embed.music.apple.com")
        return f'<iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="175" style="width:100%;max-width:660px;overflow:hidden;background:transparent;border-radius:12px;" sandbox="allow-forms allow-popups allow-others allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation" src="{embed_url}"></iframe>'
    
    # 3. 网易云音乐
    if "163.com" in url:
        sid = re.search(r'id=(\d+)', url)
        if sid:
            # 提高网易云高度 (解决控件遮挡)
            return f'<iframe frameborder="no" border="0" marginwidth="0" marginheight="0" width=330 height=110 src="//music.163.com/outchain/player?type=2&id={sid.group(1)}&auto=0&height=90"></iframe>'
    return None

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("🎧 控制中心")
    if 'user' in st.session_state:
        st.success(f"你好, **{st.session_state.user}**")
        if st.session_state.user == ADMIN_USER_NAME:
            st.warning("⚠️ 已开启管理员全权删除模式")
        if st.button("注销登录"):
            del st.session_state.user
            st.rerun()
    else:
        st.caption("请输入昵称参与挑战")

# --- 5. 主登录界面 ---
if 'user' not in st.session_state:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    with st.container():
        st.title("🎵 30天推歌挑战 · 云端空间")
        u = st.text_input("给自己的推歌之旅起个昵称:", placeholder="易特版纳")
        if st.button("开启同步挑战"):
            if u:
                st.session_state.user = u.strip()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    # --- 6. 朋友圈界面 (重中之重：UI优化) ---
    st.title("🌌 朋友圈音乐时光")
    tab1, tab2 = st.tabs(["✨ 今日打卡 / 补签", "👀 查看朋友动态"])

    # 打卡选项卡
    with tab1:
        selected_day = st.slider("选择挑战天数", 1, 30, 1)
        st.markdown(f"#### **Day {selected_day} 主题**")
        st.info(CHALLENGES[selected_day-1])
        
        with st.form("music_form", clear_on_submit=True):
            m_url = st.text_input("歌曲链接", placeholder="Apple Music 或 网易云音乐分享链接")
            m_comment = st.text_area("感想 (写点共鸣吧...)", height=100)
            submit = st.form_submit_button("同步到云端")
            
            if submit and m_url:
                try:
                    conn.table("music_challenge").upsert({
                        "day": int(selected_day),
                        "url": m_url,
                        "comment": m_comment,
                        "user_name": st.session_state.user
                    }).execute()
                    st.toast("云端同步成功!", icon="🚀")
                    st.rerun()
                except Exception as e:
                    st.error(f"同步失败: {e}")

    # 动态选项卡：视觉卡片重造
    with tab2:
        res = conn.table("music_challenge").select("*").order("created_at", desc=True).execute()
        
        if not res.data:
            st.info("目前还没有动态哦。")
        else:
            for row in res.data:
                # 判断是否应用管理员高亮样式
                is_admin = row['user_name'] == ADMIN_USER_NAME
                card_class = "music-card admin-card" if is_admin else "music-card"
                
                # --- 渲染卡片布局 (CSS + HTML) ---
                st.markdown(f"""
                <div class="{card_class}">
                    <div class="card-header">
                        <span class="user-name">👤 {row['user_name']}</span>
                        <span class="day-badge">Day {row['day']}</span>
                    </div>
                    <div class="topic-line">主题：{CHALLENGES[int(row['day'])-1]}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 卡片内部的具体内容 (播放器、评论、删除)
                with st.container():
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        player_html = get_player_html(row['url'])
                        if player_html:
                            # 渲染播放器
                            st.components.v1.html(player_html, height=180 if "apple" in row['url'] else 120)
                        else:
                            st.link_button("🔗 跳转听歌", row['url'])
                        
                        if row['comment']:
                            st.chat_message("assistant").write(row['comment'])
                        st.caption(f"🕒 发布时间: {row['created_at'][:16].replace('T', ' ')}")
                    
                    with c2:
                        # 全球删除权限：管理员账号登录后，可删除任何人的动态
                        if st.session_state.user == ADMIN_USER_NAME or row['user_name'] == st.session_state.user:
                            if st.button("🗑️", key=f"del_{row['id']}", help="删除此记录"):
                                conn.table("music_challenge").delete().eq("id", row['id']).execute()
                                st.rerun()
                st.divider()