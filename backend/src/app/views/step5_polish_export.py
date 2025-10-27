import streamlit as st
import streamlit.components.v1 as st_components
from typing import Optional

from src.app.streaming import consume_stream
from src.ui import render_cost_tracker, render_diff_view
from src.app.services import agents as ag
from src.app.services.export import (
    generate_pdf_from_html,
    generate_docx_from_html,
    generate_docx_from_code,
)
from src.app.services import persistence as persist


def _clean_markdown_wrapped(content: str) -> str:
    """Strip common triple-backtick wrappers from model output."""
    cleaned = content.strip()
    if cleaned.startswith("```html"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def render_step(*, db, client, model: str, auto_output_format: Optional[str]) -> None:
    """Render Step 5: Final Polish & Export."""
    # Auto-run polish
    if (
        st.session_state.auto_run_active
        and not st.session_state.final_resume
        and not st.session_state.get("pipeline_mode")
    ):
        format_type = (
            "docx"
            if auto_output_format == "DOCX"
            else "html"
            if auto_output_format
            else "html"
        )
        with st.spinner(
            f"🤖 Agent 5 is applying final polish (auto-run - {format_type.upper()} format)..."
        ):
            try:
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                # Use Agent 5 specific model
                agent5_model = st.session_state.get("model_agent5", model)

                stream = ag.stream_polish_resume(
                    client=client,
                    model=agent5_model,
                    optimized_resume=st.session_state.optimized_resume,
                    validation_report=st.session_state.validation_result,
                    output_format=format_type,
                )

                full_response, metadata = consume_stream(response_container, stream)

                cleaned_response = _clean_markdown_wrapped(full_response)
                st.session_state.final_resume = cleaned_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=5,
                    agent_name="Polish Agent",
                    input_data={
                        "optimized_resume": st.session_state.optimized_resume,
                        "validation_report": st.session_state.validation_result,
                    },
                    output_data={"final_resume": full_response},
                    metadata=metadata,
                    update_fields={
                        "optimized_resume_text": full_response,
                        "total_cost": st.session_state.total_cost,
                        "status": "completed",
                    },
                )

                st.success(
                    "✅ Final polish complete! (auto-run) Your resume is ready for submission."
                )
                st.session_state.auto_run_active = False
                st.rerun()

            except Exception as e:
                st.error(f"❌ Auto-run error: {str(e)}")
                st.session_state.auto_run_active = False

    # Normal UI
    st.header("✨ Step 5: Final Polish & Export")
    st.markdown(
        "Apply validator recommendations and export your submission-ready resume"
    )

    with st.expander("✅ View Validation Report", expanded=False):
        st.markdown(st.session_state.validation_result)

    with st.expander("ℹ️ What This Agent Does", expanded=False):
        st.markdown(
            """
            The **Polish Agent** will:
            - ✅ Apply all quick wins from validation
            - ✅ Fix red flags and concerns
            - ✅ Update placeholder links
            - ✅ Standardize formatting
            - ✅ Produce submission-ready resume
            """
        )

    st.markdown("### 🎯 Output Format")
    output_format = st.radio(
        "Choose output format:",
        ["DOCX (editable Word document)", "HTML (for PDF export)"],
        help="DOCX is recommended for editability and better page break control",
        horizontal=True,
    )

    format_type = "docx" if "DOCX" in output_format else "html"

    if st.button("🚀 Apply Final Polish"):
        with st.spinner("🤖 Agent 5 is applying final polish..."):
            try:
                st.markdown("### 🔄 Streaming Response")
                response_container = st.empty()

                # Use Agent 5 specific model
                agent5_model = st.session_state.get("model_agent5", model)

                stream = ag.stream_polish_resume(
                    client=client,
                    model=agent5_model,
                    optimized_resume=st.session_state.optimized_resume,
                    validation_report=st.session_state.validation_result,
                    output_format=format_type,
                )

                full_response, metadata = consume_stream(response_container, stream)

                cleaned_response = _clean_markdown_wrapped(full_response)
                st.session_state.final_resume = cleaned_response
                st.session_state.agent_costs.append(metadata.get("cost", 0))
                st.session_state.total_cost += metadata.get("cost", 0)

                persist.persist_agent_result(
                    db,
                    application_id=st.session_state.application_id,
                    agent_number=5,
                    agent_name="Polish Agent",
                    input_data={
                        "optimized_resume": st.session_state.optimized_resume,
                        "validation_report": st.session_state.validation_result,
                    },
                    output_data={"final_resume": full_response},
                    metadata=metadata,
                    update_fields={
                        "optimized_resume_text": full_response,
                        "total_cost": st.session_state.total_cost,
                        "status": "completed",
                    },
                )

                st.success(
                    "✅ Final polish complete! Your resume is ready for submission."
                )
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    if "final_resume" in st.session_state and st.session_state.final_resume:
        st.markdown("---")
        st.markdown("## 🎉 Resume Complete!")
        st.success("🎯 Your submission-ready resume is generated. Download below.")

        st.markdown("### 💰 Total Cost")
        render_cost_tracker(st.session_state.agent_costs, st.session_state.total_cost)

        resume_content = st.session_state.final_resume.strip()
        is_html = resume_content.lower().startswith(
            "<!doctype"
        ) or resume_content.lower().startswith("<html")

        if is_html:
            st.markdown("---")
            st.markdown("### 👁️ HTML Preview")
            with st.expander("👁️ View HTML Source", expanded=False):
                st.code(st.session_state.final_resume, language="html")
            with st.expander("🎨 Render HTML Preview", expanded=True):
                st_components.html(
                    st.session_state.final_resume, height=800, scrolling=True
                )
        else:
            st.markdown("---")
            st.markdown("### 📊 Before & After Comparison")
            render_diff_view(
                st.session_state.resume_text, st.session_state.final_resume
            )

        st.markdown("---")
        st.markdown("## 📥 Export Options")

        st.markdown("### 📝 Text Formats")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button(
                "📄 Final Resume (TXT)",
                data=st.session_state.final_resume,
                file_name="final_resume.txt",
                mime="text/plain",
            )
        with col2:
            if "optimization_report" in st.session_state:
                st.download_button(
                    "📋 Optimization Report",
                    data=st.session_state.optimization_report,
                    file_name="optimization_report.txt",
                    mime="text/plain",
                )
        with col3:
            st.download_button(
                "📊 Job Analysis",
                data=st.session_state.job_analysis,
                file_name="job_analysis.txt",
                mime="text/plain",
            )
        with col4:
            st.download_button(
                "✅ Validation Report",
                data=st.session_state.validation_result,
                file_name="validation_report.txt",
                mime="text/plain",
            )

        st.markdown("### 📥 Export Options")
        st.caption("🎯 Locally rendered - no additional API cost")

        resume_content = st.session_state.final_resume.strip()
        is_html = resume_content.lower().startswith(
            "<!doctype"
        ) or resume_content.lower().startswith("<html")

        if is_html:
            col_pdf, col_docx = st.columns(2)

            with col_pdf:
                _ = st.markdown("**PDF Export**")
                if st.button(
                    "🖨️ Generate PDF", help="Create a professional PDF", key="btn_pdf"
                ):
                    try:
                        with st.spinner("Generating PDF..."):
                            pdf_bytes = generate_pdf_from_html(
                                st.session_state.final_resume
                            )
                            st.session_state.pdf_ready = pdf_bytes
                            _ = st.success("✅ PDF generated!")
                    except Exception as e:
                        _ = st.error(f"❌ PDF failed: {str(e)}")

                if "pdf_ready" in st.session_state:
                    _ = st.download_button(
                        "⬇️ Download PDF",
                        data=st.session_state.pdf_ready,
                        file_name="final_resume.pdf",
                        mime="application/pdf",
                        key="dl_pdf",
                    )

            with col_docx:
                _ = st.markdown("**DOCX Export**")
                if st.button(
                    "📝 Generate DOCX", help="Convert HTML to DOCX", key="btn_docx"
                ):
                    try:
                        with st.spinner("Generating DOCX..."):
                            docx_bytes = generate_docx_from_html(
                                st.session_state.final_resume
                            )
                            st.session_state.docx_ready = docx_bytes
                            _ = st.success("✅ DOCX generated!")
                    except Exception as e:
                        _ = st.error(f"❌ DOCX failed: {str(e)}")

                if "docx_ready" in st.session_state:
                    _ = st.download_button(
                        "⬇️ Download DOCX",
                        data=st.session_state.docx_ready,
                        file_name="final_resume.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="dl_docx",
                    )
        else:
            _ = st.markdown("**DOCX Export (Code-Generated)**")
            _ = st.info(
                "✅ Your resume was generated as Python code - execute it to create DOCX!"
            )
            with st.expander("👀 View Generated Code", expanded=False):
                _ = st.code(st.session_state.final_resume, language="python")

            if st.button(
                "📝 Execute Code & Generate DOCX",
                help="Run the Python code to create DOCX",
                key="btn_exec_docx",
            ):
                try:
                    with st.spinner("Executing code and generating DOCX..."):
                        docx_bytes = generate_docx_from_code(
                            st.session_state.final_resume
                        )
                        st.session_state.docx_ready = docx_bytes
                        _ = st.success("✅ DOCX generated!")
                except Exception as e:
                    _ = st.error(f"❌ DOCX generation failed: {str(e)}")
                    _ = st.exception(e)
                    _ = st.info(
                        "💡 Tip: Check if the code is valid Python and creates a 'doc' variable"
                    )

            if "docx_ready" in st.session_state:
                _ = st.download_button(
                    "⬇️ Download DOCX",
                    data=st.session_state.docx_ready,
                    file_name="final_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
