import streamlit as st
from st_supabase_connection import SupabaseConnection
import re
import requests
from datetime import datetime

# --- 1. 基础配置与 UI 样式 ---
st.set_page_config(page_title="Music 30 Days", layout="wide", page_icon="🎵")

# 自定义 CSS 提升设计感
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stApp { max-width: 1000px; margin: 0 auto; }
    .music-card {
        padding: 20px;
        border-radius: 15px;
        background: #161b22;
        border: 1px solid #30363d;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .music-card:hover { transform: translateY(-5px); border-color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 挑战内容管理 ---
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

# 管理员设置（建议在 Secrets 中设置，这里默认为 '易特版纳'）
ADMIN_NAME = "易特版纳"

# --- 3. 解析逻辑 ---
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
            # 优化了网易云 iframe 参数 (height 提高以防止按钮遮挡)
            return f'<iframe frameborder="no" border="0" marginwidth="0" marginheight="0" width=330 height=110 src="//music.163.com/outchain/player?type=2&id={sid.group(1)}&auto=0&height=90"></iframe>'
    return None

# --- 4. 侧边栏与数据初始化 ---
conn = st.connection("supabase", type=SupabaseConnection)

with st.sidebar:
    st.title("⚙️ 设置")
    if 'user' in st.session_state:
        st.success(f"当前用户: {st.session_state.user}")
        if st.session_state.user == ADMIN_NAME:
            st.warning("⚠️ 管理员权限已开启")
        
        # 自定义挑战内容
        with st.expander("🛠️ 自定义挑战内容"):
            custom_list = st.text_area("每行一个主题 (需填满30行)", value="\n".join(DEFAULT_CHALLENGES), height=300)
            CHALLENGES = custom_list.split("\n")
            if len(CHALLENGES) < 30:
                st.error("主题不足 30 个！")
                CHALLENGES = DEFAULT_CHALLENGES
        
        if st.button("退出登录"):
            del st.session_state.user
            st.rerun()
    else:
        st.write("请先登录")

# --- 5. 主界面逻辑 ---
if 'user' not in st.session_state:
    st.title("🎧 30天推歌挑战")
    u = st.text_input("请输入昵称开始:", placeholder="易特版纳")
    if st.button("进入应用"):
        if u:
            st.session_state.user = u.strip()
            st.rerun()
else:
    tab1, tab2 = st.tabs(["✨ 新增发布", "🌌 朋友圈动态"])

    with tab1:
        st.subheader("打卡记录")
        selected_day = st.slider("选择挑战天数", 1, 30, 1)
        st.markdown(f"**Day {selected_day}:** `{DEFAULT_CHALLENGES[selected_day-1]}`")
        
        with st.form("post_form"):
            url = st.text_input("歌曲链接", placeholder="Apple Music / 网易云")
            comment = st.text_area("感想", placeholder="写下此刻的共鸣...")
            if st.form_submit_button("同步到云端"):
                if url:
                    conn.table("music_challenge").upsert({
                        "day": selected_day, "url": url, "comment": comment, "user_name": st.session_state.user
                    }).execute()
                    st.toast("同步成功!", icon="🚀")
                    st.rerun()

    with tab2:
        res = conn.table("music_challenge").select("*").order("created_at", desc=True).execute()
        for row in res.data:
            with st.container():
                # 渲染卡片布局
                st.markdown(f"""
                <div class="music-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold; font-size: 1.2rem; color: #58a6ff;">👤 {row['user_name']}</span>
                        <span style="color: #8b949e;">Day {row['day']}</span>
                    </div>
                    <div style="margin: 10px 0; color: #d1d5da; font-size: 0.9rem;">主题: {DEFAULT_CHALLENGES[int(row['day'])-1]}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    player = get_player_html(row['url'])
                    if player:
                        st.components.v1.html(player, height=180 if "apple" in row['url'] else 120)
                    else:
                        st.link_button("🚀 跳转听歌", row['url'])
                    
                    if row['comment']:
                        st.info(row['comment'])
                
                with c2:
                    # 管理员删除逻辑：本人或管理员可删除
                    if st.session_state.user == ADMIN_NAME or row['user_name'] == st.session_state.user:
                        if st.button("🗑️ 删除", key=f"del_{row['id']}"):
                            conn.table("music_challenge").delete().eq("id", row['id']).execute()
                            st.rerun()
                st.divider()