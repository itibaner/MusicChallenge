import streamlit as st
from st_supabase_connection import SupabaseConnection
import re
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="30天推歌挑战", layout="wide", page_icon="🎧")

# --- 30天主题列表 ---
CHALLENGES = [
    "歌名里带有颜色的歌", "歌名里带有数字的歌", "让你想起夏天的歌", 
    "让你想起宁愿忘记的人的歌", "需要调大音量放的歌", "让你想尽情跳舞的歌",
    "适合开车时听的歌", "关于药物或酒精的歌", "能让你感到开心的歌", "能让你感到悲伤的歌",
    "永远不会厌倦的歌", "来自你青春期前(13岁)的歌", "你喜欢的来自70年代的歌",
    "你想在婚礼上播的歌", "你喜欢的由别的艺术家翻唱的歌", "你的挚爱经典",
    "你会和某个人在KTV唱的二重唱", "发行于你出生那年的歌", "使你开始思考生活的歌",
    "对于你有很多意义的歌", "带有某人名字在你歌名中你喜欢的歌", "激励你上进的歌",
    "你觉得每个人都要听的歌", "来自你遗憾解散的乐队的歌", "你喜欢的一个已经逝去艺术家的歌",
    "让你想要陷入爱情的歌", "让你心碎的歌", "来自一位你超喜欢Ta声音的艺术家的歌",
    "一首在你童年记忆里的歌", "一首让你想起自己的歌"
]

# --- 建立 Supabase 连接 ---
# 请确保你的 .streamlit/secrets.toml 中有 SUPABASE_URL 和 SUPABASE_KEY
conn = st.connection("supabase", type=SupabaseConnection)

# --- 播放器解析逻辑 ---
def get_player_html(url):
    if not url or str(url) == "nan": return None
    # Apple Music
    if "apple.com" in url:
        embed_url = url.replace("music.apple.com", "embed.music.apple.com")
        return f'<iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="175" style="width:100%;max-width:660px;overflow:hidden;background:transparent;border-radius:10px;" src="{embed_url}"></iframe>'
    # 网易云音乐
    if "163.com" in url:
        sid = re.search(r'id=(\d+)', url)
        if sid:
            return f'<iframe frameborder="no" border="0" marginwidth="0" marginheight="0" width=330 height=86 src="//music.163.com/outchain/player?type=2&id={sid.group(1)}&auto=0&height=66"></iframe>'
    return None

# --- 用户登录系统 ---
if 'user' not in st.session_state:
    st.title("🎵 30天推歌挑战")
    st.info("数据将实时同步至云端，与朋友共同完成挑战")
    u = st.text_input("请输入你的昵称 (用于标识你的打卡)", placeholder="例如: Yite")
    if st.button("开始同步之旅"):
        if u.strip():
            st.session_state.user = u.strip()
            st.rerun()
        else:
            st.warning("请输入昵称后再继续")
else:
    user = st.session_state.user
    st.sidebar.title(f"👤 {user}")
    if st.sidebar.button("退出登录"):
        del st.session_state.user
        st.rerun()

    tab1, tab2 = st.tabs(["✍️ 今日打卡 / 补签", "🌍 朋友圈动态"])

    # --- 选项卡 1: 打卡功能 ---
    with tab1:
        st.subheader("记录你的音乐心情")
        # 补签逻辑：自由选择天数
        selected_day = st.number_input("选择挑战天数 (Day 1 - 30)", 1, 30, 1)
        st.markdown(f"### **Day {selected_day} 主题**")
        st.success(CHALLENGES[selected_day-1])
        
        with st.form("music_form", clear_on_submit=False):
            m_url = st.text_input("歌曲链接", placeholder="粘贴 Apple Music 或 网易云音乐链接")
            m_comment = st.text_area("为什么推荐这首歌？", placeholder="写点什么吧...", height=100)
            submit = st.form_submit_button("同步到云端")
            
            if submit:
                if m_url:
                    try:
                        # 插入或更新数据
                        # 注意：我们在 SQL 里没设联合唯一约束，这里简单演示插入
                        conn.table("music_challenge").upsert({
                            "day": int(selected_day),
                            "url": m_url,
                            "comment": m_comment,
                            "user_name": user
                        }).execute()
                        st.balloons()
                        st.success(f"Day {selected_day} 同步成功！")
                    except Exception as e:
                        st.error(f"同步失败: {e}")
                else:
                    st.error("请至少提供一个歌曲链接")

    # --- 选项卡 2: 朋友圈展示 ---
    with tab2:
        st.subheader("大家最近在听...")
        try:
            # 从 Supabase 读取所有数据，按创建时间倒序排
            response = conn.table("music_challenge").select("*").order("created_at", desc=True).execute()
            rows = response.data
            
            if not rows:
                st.info("目前还没有动态，快去发布第一首歌吧！")
            else:
                for row in rows:
                    with st.container():
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            # 修复之前显示 nan 的问题
                            display_name = str(row['user_name']) if row['user_name'] else "匿名好友"
                            st.markdown(f"#### {display_name}")
                            st.markdown(f"`Day {row['day']}`")
                        with c2:
                            st.caption(f"主题: {CHALLENGES[int(row['day'])-1]}")
                            player = get_player_html(row['url'])
                            if player:
                                st.components.v1.html(player, height=180 if "apple" in row['url'] else 100)
                            else:
                                st.warning("链接解析失败")
                                st.link_button("跳转链接", row['url'])
                            
                            if row['comment']:
                                st.chat_message("assistant").write(row['comment'])
                        st.divider()
        except Exception as e:
            st.error(f"读取数据失败: {e}")