import streamlit as st
from st_supabase_connection import SupabaseConnection
import re
import requests
from datetime import datetime

# --- 1. 高级 UI 配置与自动色彩适配 ---
st.set_page_config(page_title="Music 30 Days", layout="wide", page_icon="🎧")

# 自动适配深浅色模式的 CSS
# 使用 rgba 和半透明度，确保在深浅背景下都有良好的层次感
st.markdown("""
    <style>
    /* 全局容器限制 */
    .stApp { max-width: 900px; margin: 0 auto; }
    
    /* 动态音乐卡片：背景色使用半透明，边框使用动态颜色 */
    .music-card {
        background-color: rgba(128, 128, 128, 0.08);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 25px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    /* 悬停效果：根据系统主色调产生呼吸感 */
    .music-card:hover {
        transform: translateY(-4px);
        border-color: #58a6ff;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    /* 管理员卡片：特殊的金色渐变边框 */
    .admin-card {
        border: 2px solid #f1c40f !important;
        background: linear-gradient(145deg, rgba(241,196,15,0.05), rgba(128,128,128,0.08));
    }
    
    /* 文字颜色适配 */
    .user-name { font-weight: 800; font-size: 1.15rem; color: #58a6ff; }
    .day-badge { 
        background: #238636; 
        color: white; 
        padding: 2px 10px; 
        border-radius: 20px; 
        font-size: 0.75rem; 
        float: right;
    }
    .topic-text { 
        margin: 10px 0; 
        font-size: 0.95rem; 
        opacity: 0.8;
        font-weight: 500;
    }
    
    /* 响应式调整 */
    @media (max-width: 640px) {
        .music-card { padding: 15px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心数据与权限 (修正变量名错误) ---
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

# 从 Secrets 安全读取管理员名称 (统一变量名为 ADMIN_NAME)
ADMIN_NAME = st.secrets.get("ADMIN_USER", "")

# --- 3. 核心连接与解析 (保持网易云/AM兼容) ---
conn = st.connection("supabase", type=SupabaseConnection)

def get_player_url(url):
    if not url or str(url) == "nan": return None
    url = str(url).strip()
    
    # 还原短链接
    if "163cn.tv" in url:
        try:
            res = requests.get(url, allow_redirects=True, timeout=5)
            url = res.url
        except: pass

    # 解析返回纯链接供 st.iframe 使用
    if "music.apple.com" in url:
        return url.split('?')[0].replace("music.apple.com", "embed.music.apple.com")
    
    if "163.com" in url:
        sid = re.search(r'id=(\d+)', url)
        if sid:
            return f"https://music.163.com/outchain/player?type=2&id={sid.group(1)}&auto=0&height=90"
    return None

# --- 4. 侧边栏 ---
with st.sidebar:
    st.title("🛡️ 权限中心")
    if 'user' in st.session_state:
        st.write(f"当前用户: **{st.session_state.user}**")
        if st.session_state.user == ADMIN_NAME:
            st.warning("已激活管理员全屏删除模式")
        if st.button("退出登录"):
            del st.session_state.user
            st.rerun()

# --- 5. 主逻辑界面 ---
if 'user' not in st.session_state:
    st.title("🎵 30天推歌挑战 · 空间")
    u = st.text_input("给自己起个昵称:", placeholder="例如：用户名")
    if st.button("进入系统") and u.strip():
        st.session_state.user = u.strip()
        st.rerun()
else:
    tab1, tab2 = st.tabs(["✨ 新增发布", "🌌 朋友圈动态"])

    with tab1:
        selected_day = st.slider("选择天数", 1, 30, 1)
        st.markdown(f"#### Day {selected_day}: {CHALLENGES[selected_day-1]}")
        with st.form("post_form", clear_on_submit=True):
            m_url = st.text_input("歌曲链接 (AM/网易云)")
            m_note = st.text_area("感想...")
            if st.form_submit_button("发送同步"):
                if m_url:
                    conn.table("music_challenge").upsert({
                        "day": int(selected_day), 
                        "url": m_url, 
                        "comment": m_note, 
                        "user_name": st.session_state.user
                    }).execute()
                    st.toast("发布成功!")
                    st.rerun()

    with tab2:
        res = conn.table("music_challenge").select("*").order("created_at", desc=True).execute()
        
        for row in res.data:
            # 判断是否为管理员或本人，显示金色边框
            is_admin_post = (row['user_name'] == ADMIN_NAME)
            card_style = "admin-card" if is_admin_post else ""
            
            # --- 结构化卡片渲染 ---
            st.markdown(f"""
            <div class="music-card {card_style}">
                <div class="user-name">
                    👤 {row['user_name']}
                    <span class="day-badge">Day {row['day']}</span>
                </div>
                <div class="topic-text">主题：{CHALLENGES[int(row['day'])-1]}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 播放器与操作
            col_main, col_del = st.columns([5, 1])
            with col_main:
                player_url = get_player_url(row['url'])
                if player_url:
                    st.iframe(src=player_url, height=180 if "apple" in player_url else 120)
                else:
                    st.link_button("🚀 直接听歌", row['url'])
                
                if row['comment']:
                    st.chat_message("user").write(row['comment'])
                st.caption(f"🕒 {row['created_at'][:16].replace('T', ' ')}")

            with col_del:
                # 管理员或发布者本人拥有删除按钮
                if st.session_state.user == ADMIN_NAME or row['user_name'] == st.session_state.user:
                    if st.button("🗑️", key=f"del_{row['id']}", help="删除此项"):
                        conn.table("music_challenge").delete().eq("id", row['id']).execute()
                        st.rerun()
            st.divider()
