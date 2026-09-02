"""
게시판 UI (Streamlit)
- 자유게시판 / 오류보고·기능요청 2개 보드
- call_api, API_BASE, st.session_state.token 은 app.py에서 주입됨
"""
import streamlit as st


_BOARD_META = {
    "free":   {"label": "💬 자유게시판",       "icon": "💬"},
    "report": {"label": "🐛 오류보고·기능요청", "icon": "🐛"},
}

_STATUS_COLOR = {
    "접수중": "#90a4ae",
    "확인됨": "#42a5f5",
    "처리중": "#ffa726",
    "완료":   "#66bb6a",
    "보류":   "#ef5350",
    "일반":   "#bdbdbd",
}

_CAT_OPTIONS = ["버그", "기능요청", "기타"]
_STATUS_OPTIONS = ["접수중", "확인됨", "처리중", "완료", "보류"]


def _badge(text: str, color: str) -> str:
    return (
        f"<span style='background:{color};color:#fff;border-radius:4px;"
        f"padding:1px 7px;font-size:0.72rem;font-weight:600;'>{text}</span>"
    )


def _pin_badge() -> str:
    return (
        "<span style='background:#1565c0;color:#fff;border-radius:4px;"
        "padding:1px 7px;font-size:0.72rem;font-weight:600;'>📌 공지</span>"
    )


def show_board(call_api, is_admin: bool = False):
    """게시판 탭 메인 진입점"""
    # 현재 보드 선택
    _board_keys = list(_BOARD_META.keys())
    _board_labels = [v["label"] for v in _BOARD_META.values()]
    _sel_idx = st.session_state.get("_board_sel_idx", 0)
    cols = st.columns(len(_BOARD_META))
    for i, (k, v) in enumerate(_BOARD_META.items()):
        with cols[i]:
            if st.button(v["label"], use_container_width=True,
                         type="primary" if _sel_idx == i else "secondary",
                         key=f"_brd_sel_{k}"):
                st.session_state["_board_sel_idx"] = i
                st.session_state.pop("_board_post_id", None)
                st.rerun()

    board_type = _board_keys[_sel_idx]
    post_id = st.session_state.get("_board_post_id")

    if post_id:
        _show_post_detail(call_api, board_type, post_id, is_admin)
    else:
        _show_post_list(call_api, board_type, is_admin)


# ── 목록 ────────────────────────────────────────────────────────
def _show_post_list(call_api, board_type: str, is_admin: bool):
    col_title, col_btn = st.columns([5, 1])
    with col_title:
        st.subheader(_BOARD_META[board_type]["label"])
    with col_btn:
        if st.button("✏️ 글쓰기", use_container_width=True, type="primary"):
            st.session_state["_board_writing"] = True
            st.rerun()

    # 글쓰기 폼
    if st.session_state.pop("_board_writing", False):
        _write_form(call_api, board_type)
        return

    page = st.session_state.get(f"_brd_page_{board_type}", 1)
    data, err = call_api(f"/boards/{board_type}/posts?page={page}&per_page=20", method="GET")
    if err:
        st.error(err)
        return

    posts = data.get("posts", [])
    total = data.get("total", 0)

    if not posts:
        st.info("아직 게시글이 없습니다. 첫 글을 작성해 보세요!")
        return

    st.markdown(f"<small style='color:#888;'>총 {total}개 게시글</small>", unsafe_allow_html=True)

    for p in posts:
        with st.container():
            badges = ""
            if p.get("is_pinned"):
                badges += _pin_badge() + " "
            if board_type == "report":
                cat = p.get("category") or "기타"
                st_val = p.get("status", "접수중")
                badges += _badge(cat, "#5c6bc0") + " "
                badges += _badge(st_val, _STATUS_COLOR.get(st_val, "#90a4ae")) + " "

            title_html = (
                f"<div style='display:flex;align-items:center;gap:6px;flex-wrap:wrap;'>"
                f"{badges}<span style='font-weight:600;font-size:1rem;cursor:pointer;'>"
                f"{p['title']}</span>"
                f"<small style='color:#888;margin-left:auto;'>"
                f"💬 {p.get('comment_count',0)} &nbsp; 👁 {p.get('view_count',0)}</small>"
                f"</div>"
                f"<div style='font-size:0.78rem;color:#aaa;margin-top:2px;'>"
                f"{p['author_name']} · {p['created_at']}"
                f"</div>"
            )
            st.markdown(html_sep := "<hr style='margin:4px 0;border:none;border-top:1px solid rgba(128,128,128,0.15);'>",
                        unsafe_allow_html=True)
            st.markdown(title_html, unsafe_allow_html=True)
            if st.button("→ 읽기", key=f"_post_{p['id']}", use_container_width=False):
                st.session_state["_board_post_id"] = p["id"]
                st.rerun()

    # 페이지 이동
    total_pages = max(1, (total + 19) // 20)
    if total_pages > 1:
        pcols = st.columns([1, 2, 1])
        with pcols[0]:
            if page > 1:
                if st.button("◀ 이전", use_container_width=True):
                    st.session_state[f"_brd_page_{board_type}"] = page - 1
                    st.rerun()
        with pcols[1]:
            st.markdown(f"<div style='text-align:center;padding-top:6px;'>{page} / {total_pages}</div>",
                        unsafe_allow_html=True)
        with pcols[2]:
            if page < total_pages:
                if st.button("다음 ▶", use_container_width=True):
                    st.session_state[f"_brd_page_{board_type}"] = page + 1
                    st.rerun()


# ── 글쓰기 폼 ───────────────────────────────────────────────────
def _write_form(call_api, board_type: str, post: dict | None = None):
    is_edit = post is not None
    st.subheader("✏️ " + ("글 수정" if is_edit else "글 쓰기"))

    with st.form("_board_write_form"):
        if board_type == "report":
            cat = st.selectbox("카테고리", _CAT_OPTIONS,
                               index=_CAT_OPTIONS.index(post["category"]) if is_edit and post.get("category") else 0)
        else:
            cat = None

        title = st.text_input("제목", value=post["title"] if is_edit else "")
        content = st.text_area("내용", value=post["content"] if is_edit else "", height=220)

        c1, c2 = st.columns(2)
        submitted = c1.form_submit_button("저장", type="primary", use_container_width=True)
        cancelled = c2.form_submit_button("취소", use_container_width=True)

    if cancelled:
        st.rerun()

    if submitted:
        if not title.strip():
            st.error("제목을 입력하세요.")
            return
        if not content.strip():
            st.error("내용을 입력하세요.")
            return

        payload = {"title": title.strip(), "content": content.strip()}
        if cat:
            payload["category"] = cat

        if is_edit:
            _, err = call_api(f"/boards/{board_type}/posts/{post['id']}", payload, method="PUT")
        else:
            _, err = call_api(f"/boards/{board_type}/posts", payload, method="POST")

        if err:
            st.error(f"저장 실패: {err}")
        else:
            st.toast("✅ 저장되었습니다.")
            st.session_state.pop("_board_post_id", None)
            st.rerun()


# ── 글 상세 ─────────────────────────────────────────────────────
def _show_post_detail(call_api, board_type: str, post_id: int, is_admin: bool):
    user_id = st.session_state.get("user_id")

    data, err = call_api(f"/boards/{board_type}/posts/{post_id}", method="GET")
    if err:
        st.error(err)
        if st.button("← 목록으로"):
            st.session_state.pop("_board_post_id", None)
            st.rerun()
        return

    # 수정 모드
    if st.session_state.get("_board_editing"):
        _write_form(call_api, board_type, data)
        return

    # 헤더
    col_back, col_actions = st.columns([1, 3])
    with col_back:
        if st.button("← 목록"):
            st.session_state.pop("_board_post_id", None)
            st.rerun()

    badges = ""
    if data.get("is_pinned"):
        badges += _pin_badge() + " "
    if board_type == "report":
        cat = data.get("category") or "기타"
        st_val = data.get("status", "접수중")
        badges += _badge(cat, "#5c6bc0") + " "
        badges += _badge(st_val, _STATUS_COLOR.get(st_val, "#90a4ae")) + " "

    st.markdown(
        f"<h3 style='margin:0.3rem 0 0.1rem 0;'>{badges}{data['title']}</h3>"
        f"<div style='font-size:0.82rem;color:#aaa;'>"
        f"{data['author_name']} · {data['created_at']} · 조회 {data['view_count']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # 본문
    st.markdown(data["content"].replace("\n", "  \n"))
    st.markdown("---")

    # 관리자 / 작성자 액션
    is_mine = data.get("user_id") == user_id
    action_cols = st.columns(4)
    with action_cols[0]:
        if (is_mine or is_admin) and st.button("✏️ 수정"):
            st.session_state["_board_editing"] = True
            st.rerun()
    with action_cols[1]:
        if (is_mine or is_admin) and st.button("🗑️ 삭제"):
            st.session_state["_board_confirm_delete_post"] = True
            st.rerun()
    with action_cols[2]:
        if is_admin and board_type == "report":
            new_status = st.selectbox("상태 변경", _STATUS_OPTIONS,
                                      index=_STATUS_OPTIONS.index(data.get("status", "접수중"))
                                      if data.get("status") in _STATUS_OPTIONS else 0,
                                      key="_brd_status_sel", label_visibility="collapsed")
            if st.button("상태 저장"):
                _, e = call_api(
                    f"/boards/{board_type}/posts/{post_id}/status",
                    {"status": new_status}, method="PATCH"
                )
                if not e:
                    st.toast("상태 변경 완료")
                    st.rerun()
    with action_cols[3]:
        if is_admin:
            pin_label = "📌 고정 해제" if data.get("is_pinned") else "📌 공지 고정"
            if st.button(pin_label):
                call_api(f"/boards/{board_type}/posts/{post_id}/pin", method="PATCH")
                st.rerun()

    # 삭제 확인
    if st.session_state.pop("_board_confirm_delete_post", False):
        with st.container():
            st.warning("정말 삭제하시겠습니까?")
            dc1, dc2 = st.columns(2)
            if dc1.button("삭제 확인", type="primary"):
                _, e = call_api(f"/boards/{board_type}/posts/{post_id}", method="DELETE")
                if not e:
                    st.toast("삭제되었습니다.")
                    st.session_state.pop("_board_post_id", None)
                    st.rerun()
            if dc2.button("취소"):
                st.rerun()
        return

    # ── 댓글 섹션 ──────────────────────────────────────────────
    comments = data.get("comments", [])
    st.markdown(f"**댓글 {len(comments)}개**")

    for c in comments:
        is_my_comment = c.get("user_id") == user_id
        with st.container():
            c_col1, c_col2 = st.columns([8, 1])
            with c_col1:
                st.markdown(
                    f"<div style='font-size:0.82rem;font-weight:600;'>{c['author_name']}"
                    f" <span style='font-weight:400;color:#aaa;'>{c['created_at']}</span></div>"
                    f"<div style='margin:2px 0 6px 0;'>{c['content'].replace(chr(10), '<br>')}</div>",
                    unsafe_allow_html=True,
                )
            with c_col2:
                if is_my_comment or is_admin:
                    if st.button("🗑️", key=f"_del_cmt_{c['id']}", help="댓글 삭제"):
                        call_api(
                            f"/boards/{board_type}/posts/{post_id}/comments/{c['id']}",
                            method="DELETE"
                        )
                        st.rerun()

    # 댓글 작성
    st.markdown("---")
    with st.form("_brd_comment_form", clear_on_submit=True):
        cmt_text = st.text_area("댓글 작성", placeholder="댓글을 입력하세요...", height=80,
                                label_visibility="collapsed")
        if st.form_submit_button("댓글 등록", type="primary"):
            if cmt_text.strip():
                _, e = call_api(
                    f"/boards/{board_type}/posts/{post_id}/comments",
                    {"content": cmt_text.strip()}
                )
                if e:
                    st.error(e)
                else:
                    st.rerun()
            else:
                st.warning("댓글 내용을 입력하세요.")
