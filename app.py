import streamlit as st
from st_supabase_connection import SupabaseConnection
import re
import requests
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
conn = st.connection("supabase", type=SupabaseConnection)

# --- 解析函数 ---
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
        return f'<iframe allow="autoplay *; encrypted-media *; fullscreen *; clipboard-write" frameborder="0" height="175" style="width:100%;max-width:660px;overflow:hidden;background:transparent;border-radius:10px;" src="{embed_url}"></iframe>'
    
    if "163.com" in url:
        sid = re.search(r'id=(\d+)', url)
        if sid:
            return f'<iframe frameborder="no" border="0" marginwidth="0" marginheight="0" width=330 height=86 src="//music.163.com/outchain/player?type=2&id={sid.group(1)}&auto=0&height=66"></iframe>'
    return None

# --- 用户系统 ---
if 'user' not in st.session_state:
    st.title("🎵 30天推歌挑战")
    u = st.text_input("请输入你的昵称", placeholder="例如: 易特版纳")
    if st.button("开始挑战"):
        if u.strip():
            st.session_state.user = u.strip()
            st.rerun()
else:
    user = st.session_state.user
    st.sidebar.title(f"👤 {user}")
    if st.sidebar.button("退出登录"):
        del st.session_state.user
        st.rerun()

    tab1, tab2 = st.tabs(["✍️ 打卡 / 补签", "🌍 朋友圈动态"])

    # --- TAB 1: 打卡 ---
    with tab1:
        st.subheader("记录今日推歌")
        selected_day = st.number_input("选择挑战天数", 1, 30, 1)
        st.info(f"Day {selected_day}: {CHALLENGES[selected_day-1]}")
        
        with st.form("music_form", clear_on_submit=True):
            m_url = st.text_input("歌曲链接", placeholder="Apple Music / 网易云")
            m_comment = st.text_area("此刻的想法...")
            submit = st.form_submit_button("同步到云端")
            
            if submit and m_url:
                try:
                    conn.table("music_challenge").upsert({
                        "day": int(selected_day),
                        "url": m_url,
                        "comment": m_comment,
                        "user_name": user
                    }).execute()
                    st.success(f"Day {selected_day} 已成功同步！")
                    st.cache_data.clear() # 清除缓存
                except Exception as e:
                    st.error(f"同步失败: {e}")

    # --- TAB 2: 朋友圈 & 删除功能 ---
    with tab2:
        st.subheader("大家最近在听...")
        try:
            response = conn.table("music_challenge").select("*").order("created_at", desc=True).execute()
            rows = response.data
            
            if not rows:
                st.info("目前还没有动态。")
            else:
                for row in rows:
                    with st.container():
                        c1, c2 = st.columns([1, 4])
                        with c1:
                            st.markdown(f"#### {row['user_name']}")
                            st.markdown(f"`Day {row['day']}`")
                            
                            # --- 删除功能逻辑 ---
                            # 只有发布者本人可以看到并执行删除
                            if row['user_name'] == user:
                                if st.button("🗑️ 删除", key=f"del_{row['id']}"):
                                    conn.table("music_challenge").delete().eq("id", row['id']).execute()
                                    st.toast("记录已删除！")
                                    st.rerun() # 重新刷新页面以更新列表
                                    
                        with c2:
                            st.caption(f"主题: {CHALLENGES[int(row['day'])-1]}")
                            player_html = get_player_html(row['url'])
                            
                            if player_html:
                                st.components.v1.html(player_html, height=180 if "apple" in str(row['url']) else 100)
                            else:
                                st.link_button("🚀 直接跳转听歌", row['url'])
                            
                            if row['comment']:
                                st.info(row['comment'])
                            st.caption(f"🕒 发布时间: {row['created_at'][:16].replace('T', ' ')}")
                        st.divider()
        except Exception as e:
            st.error(f"数据获取失败: {e}")