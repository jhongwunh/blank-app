# pages/3_🔧_Preprocessing_Configurator.py
import re
import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Pre-processing Configurator", layout="wide")

# -----------------------
# Helpers
# -----------------------
HASHTAG_RE = re.compile(r"#\w+")
PUNCT_ONLY_RE = re.compile(r"^[\W_]+$")  # strings with no letters/digits after strip

def split_sentences_basic(text: str) -> list[str]:
    """Minimalist sentence splitter on ., !, ? plus newlines. Keeps order, trims blanks."""
    if not isinstance(text, str):
        return []
    # normalize newlines to space to avoid empty splits
    text = text.replace("\n", " ").strip()
    # put a space after sentence enders to improve splitting on multiple punctuations
    # then split on (?<=[.!?])\s+
    parts = re.split(r'(?<=[.!?])\s+', text)
    # Clean and filter
    return [p.strip() for p in parts if p and not PUNCT_ONLY_RE.match(p.strip())]

def extract_hashtags(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    return HASHTAG_RE.findall(text)

def remove_hashtags(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return HASHTAG_RE.sub("", text)

def is_punct_only(s: str) -> bool:
    s = (s or "").strip()
    return (not s) or bool(PUNCT_ONLY_RE.match(s))

def join_context(lines: list[str]) -> str:
    lines = [ln for ln in lines if ln and not is_punct_only(ln)]
    return " ".join(lines).strip()

def build_rows_sentence_level_chat(df, id_col, text_col, turn_col=None, speaker_col=None,
                                   rolling_N=2, whole_context=False,
                                   keep_hashtags=True, combine_hashtags=True):
    """
    Build sentence-level rows for one-to-one chat.
    Output columns: ID, Turn, Sentence, Speaker, Context, Statement
    """
    out = []

    # Group by ID (chat)
    for chat_id, g in df.groupby(id_col, sort=False):
        # sort by turn if provided; else keep input order as "turn"
        if turn_col and turn_col in g.columns:
            g = g.sort_values(by=turn_col, kind="stable")
            turns = list(g[turn_col].tolist())
        else:
            g = g.reset_index(drop=True)
            turns = list(range(1, len(g) + 1))

        turn_texts = g[text_col].fillna("").tolist()
        speakers = g[speaker_col].fillna("").tolist() if speaker_col and speaker_col in g.columns else [""] * len(g)

        # Build a flat list of (turn_no, speaker, sentence_list)
        flat_sentences = []  # [(turn, speaker, sentence_text), ...]
        for t_no, spk, raw in zip(turns, speakers, turn_texts):
            tags = extract_hashtags(raw) if keep_hashtags else []
            nohash = remove_hashtags(raw) if keep_hashtags else raw

            # split into sentences
            sents = split_sentences_basic(nohash)

            # optionally append hashtags as one consolidated sentence or many
            if keep_hashtags and tags:
                if combine_hashtags:
                    sents.append(" ".join(tags))
                else:
                    sents.extend(tags)

            # filter punctuation-only (after hashtag handling)
            sents = [s for s in sents if not is_punct_only(s)]

            for s in sents:
                flat_sentences.append((t_no, spk, s))

        # Build rolling/whole context for each sentence
        for idx, (t_no, spk, stmt) in enumerate(flat_sentences, start=1):
            if whole_context:
                # context = ALL previous + current within the chat (up to the final post/chat if desired)
                ctx_list = [s for _, _, s in flat_sentences[:idx]]
            else:
                # rolling N previous sentences *before* current
                start = max(0, idx - (rolling_N + 1))  # include up to N previous sentences
                ctx_list = [s for _, _, s in flat_sentences[start:idx]]

            context_text = join_context(ctx_list)

            out.append({
                "ID": chat_id,
                "Turn": t_no,
                "Sentence": idx,       # sentence index within the chat stream
                "Speaker": spk,
                "Context": context_text,
                "Statement": stmt
            })
    return pd.DataFrame(out)

def build_rows_turn_level_chat(df, id_col, text_col, turn_col=None, speaker_col=None,
                               rolling_N=2, whole_context=False):
    """
    Turn-level statements (each row is the whole turn text).
    """
    out = []
    for chat_id, g in df.groupby(id_col, sort=False):
        if turn_col and turn_col in g.columns:
            g = g.sort_values(by=turn_col, kind="stable")
            turns = g[turn_col].tolist()
        else:
            g = g.reset_index(drop=True)
            turns = list(range(1, len(g) + 1))

        texts = g[text_col].fillna("").tolist()
        speakers = g[speaker_col].fillna("").tolist() if speaker_col and speaker_col in g.columns else [""] * len(g)

        # Build context per turn
        for i, (t_no, spk, txt) in enumerate(zip(turns, speakers, texts), start=1):
            if whole_context:
                ctx_list = texts[:i]  # up to current
            else:
                start = max(0, i - 1 - rolling_N)  # N previous turns only
                ctx_list = texts[start:i]

            out.append({
                "ID": chat_id,
                "Turn": t_no,
                "Sentence": i,         # here, Sentence ID mirrors the turn index
                "Speaker": spk,
                "Context": join_context(ctx_list),
                "Statement": txt.strip()
            })
    res = pd.DataFrame(out)
    # drop punctuation-only statement rows
    if not res.empty:
        res = res[~res["Statement"].map(is_punct_only)]
    return res

def build_rows_sentence_level_post(df, id_col, text_col,
                                   rolling_N=2, whole_context=False,
                                   keep_hashtags=True, combine_hashtags=True):
    """
    One-to-many (social post): no speaker, no true turn;
    Turn and Sentence indices are the same by spec.
    """
    out = []
    for post_id, g in df.groupby(id_col, sort=False):
        raw = " ".join(g[text_col].fillna("").astype(str).tolist())  # if multiple rows per ID, concatenate
        tags = extract_hashtags(raw) if keep_hashtags else []
        nohash = remove_hashtags(raw) if keep_hashtags else raw
        sents = split_sentences_basic(nohash)

        if keep_hashtags and tags:
            if combine_hashtags:
                sents.append(" ".join(tags))
            else:
                sents.extend(tags)

        sents = [s for s in sents if not is_punct_only(s)]

        for i, stmt in enumerate(sents, start=1):
            if whole_context:
                ctx_list = sents[:i]
            else:
                start = max(0, i - 1 - rolling_N)
                ctx_list = sents[start:i]

            out.append({
                "ID": post_id,
                "Turn": i,
                "Sentence": i,
                "Speaker": "salesperson",  # per brief example; can be left blank if preferred
                "Context": join_context(ctx_list),
                "Statement": stmt
            })
    return pd.DataFrame(out)

# -----------------------
# UI
# -----------------------
st.title("🔧 PA7 Pre‑processing Configurator")
st.caption("Choose statement & context cuts; handle hashtags; output standardized schema (ID, Turn, Sentence, Speaker, Context, Statement).")

uploaded = st.file_uploader("Upload a CSV", type=["csv"])

if uploaded:
    df = pd.read_csv(uploaded)
    st.success(f"Loaded {len(df):,} rows.")
    with st.expander("Preview source (first 20 rows)"):
        st.dataframe(df.head(20), use_container_width=True)

    cols = df.columns.tolist()
    id_col = st.selectbox("ID column (required)", options=cols, index=0 if cols else None)
    text_col = st.selectbox("Text / Statement column (required)", options=cols, index=min(1, len(cols)-1) if cols else None)

    turn_col = st.selectbox("Turn column (optional)", options=["<none>"] + cols, index=0)
    turn_col = None if turn_col == "<none>" else turn_col

    speaker_col = st.selectbox("Speaker column (optional)", options=["<none>"] + cols, index=0)
    speaker_col = None if speaker_col == "<none>" else speaker_col

    # Infer data type
    inferred_type = "One-to-one (chat)" if turn_col else "One-to-many (post)"
    data_type = st.radio("Data type", ["One-to-one (chat)", "One-to-many (post)"], index=0 if inferred_type=="One-to-one (chat)" else 1, horizontal=True)

    statement_cut = st.radio("Statement cut", ["Sentence-level", "Turn/Post-level"], horizontal=True,
                             index=0 if data_type=="One-to-many (post)" else 0)  # sentence-level default

    context_cut = st.radio("Context cut", ["Rolling window up to statement", "Whole chat/post"], horizontal=True)
    whole_context = (context_cut == "Whole chat/post")
    rolling_N = 2
    if not whole_context:
        rolling_N = st.number_input("Rolling window size (number of previous sentences/turns)", min_value=0, max_value=50, value=2, step=1)

    st.divider()
    st.subheader("Hashtag & cleaning rules")
    keep_hashtags = st.toggle("Retain hashtags as separate sentence(s)", value=True)
    combine_hashtags = st.toggle("Combine all hashtags into one sentence (off = one row per hashtag)", value=True)

    st.caption("Punctuation-only statements will be removed automatically.")

    st.divider()
    run = st.button("▶️ Build pre‑processed dataset")

    if run:
        if not id_col or not text_col:
            st.error("Please choose ID and Text columns.")
        else:
            if data_type == "One-to-many (post)":
                # post: Turn/Post-level just means "don’t split sentences"—but PA7 examples expect sentence-level for posts.
                if statement_cut == "Sentence-level":
                    res = build_rows_sentence_level_post(
                        df, id_col, text_col,
                        rolling_N=rolling_N, whole_context=whole_context,
                        keep_hashtags=keep_hashtags, combine_hashtags=combine_hashtags
                    )
                else:
                    # Post-level: treat entire post as one statement (turn/sentence=1)
                    out = []
                    for post_id, g in df.groupby(id_col, sort=False):
                        raw = " ".join(g[text_col].fillna("").astype(str).tolist())
                        if keep_hashtags:
                            raw_nohash = remove_hashtags(raw)
                            tags = extract_hashtags(raw)
                            if combine_hashtags and tags:
                                raw_nohash = (raw_nohash + " " + " ".join(tags)).strip()
                            elif tags:
                                # add as separate rows below (turn=2..)
                                rows = [raw_nohash] + ([" ".join(tags)] if combine_hashtags else tags)
                            else:
                                rows = [raw_nohash]
                        else:
                            rows = [raw]

                        rows = [r for r in rows if not is_punct_only(r)]
                        for i, stmt in enumerate(rows, start=1):
                            ctx_list = rows[:i] if whole_context else rows[max(0, i-1-rolling_N):i]
                            out.append({
                                "ID": post_id,
                                "Turn": i,
                                "Sentence": i,
                                "Speaker": "salesperson",
                                "Context": join_context(ctx_list),
                                "Statement": stmt
                            })
                    res = pd.DataFrame(out)

            else:
                # one-to-one (chat)
                if statement_cut == "Sentence-level":
                    res = build_rows_sentence_level_chat(
                        df, id_col, text_col, turn_col=turn_col, speaker_col=speaker_col,
                        rolling_N=rolling_N, whole_context=whole_context,
                        keep_hashtags=keep_hashtags, combine_hashtags=combine_hashtags
                    )
                else:
                    res = build_rows_turn_level_chat(
                        df, id_col, text_col, turn_col=turn_col, speaker_col=speaker_col,
                        rolling_N=rolling_N, whole_context=whole_context
                    )

            if res.empty:
                st.warning("No rows produced. Check your column selections and options.")
            else:
                st.success(f"Built {len(res):,} rows.")
                st.dataframe(res.head(50), use_container_width=True)

                # Download
                buf = io.StringIO()
                res.to_csv(buf, index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=buf.getvalue(),
                    file_name="preprocessed_PA7.csv",
                    mime="text/csv"
                )

else:
    st.info("Upload a CSV to begin.")
