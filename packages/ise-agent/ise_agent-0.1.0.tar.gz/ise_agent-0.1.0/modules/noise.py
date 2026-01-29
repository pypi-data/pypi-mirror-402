import logging
import warnings


def suppress_noisy_logs():
    """
    统一降噪：屏蔽常见第三方库的 warning / log（不影响真正异常抛出）。
    目标：让 build_kb / main 的输出更干净，便于 debug。
    """
    # --- warnings ---
    warnings.filterwarnings("ignore", message=r".*`torch_dtype` is deprecated!.*")

    try:
        from langchain_core._api.deprecation import LangChainDeprecationWarning  # type: ignore

        warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
    except Exception:
        # langchain 版本不一致时忽略
        pass

    # --- logging ---
    for name in [
        "pypdf",  # "Ignoring wrong pointing object ..."
        "PyPDF2",
        "urllib3",
        "httpx",
        "langchain",
        "chromadb",
        "sentence_transformers",
        "transformers",
    ]:
        logging.getLogger(name).setLevel(logging.ERROR)


