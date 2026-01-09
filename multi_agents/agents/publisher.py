from .utils.file_formats import \
    write_md_to_pdf, \
    write_md_to_word, \
    write_text_to_md

from .utils.views import print_agent_output


class PublisherAgent:
    def __init__(self, output_dir: str, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.output_dir = output_dir.strip()
        self.headers = headers or {}
        
    async def publish_research_report(self, research_state: dict, publish_formats: dict):
        layout = self.generate_layout(research_state)
        await self.write_report_by_formats(layout, publish_formats)

        return layout

    def generate_layout(self, research_state: dict):
        task = research_state.get("task", {})
        required_sections = (task.get("output_format") or {}).get("required_sections", [])
        expert_panel = research_state.get("expert_panel") or {}
        custom_sections = self._build_required_sections(required_sections, expert_panel)
        sections = []
        for subheader in research_state.get("research_data", []):
            if isinstance(subheader, dict):
                # Handle dictionary case
                for key, value in subheader.items():
                    sections.append(f"{value}")
            else:
                # Handle string case
                sections.append(f"{subheader}")
        
        sections_text = '\n\n'.join(sections)
        custom_sections_text = "\n\n".join(custom_sections)
        references = '\n'.join(f"{reference}" for reference in research_state.get("sources", []))
        headers = research_state.get("headers", {})
        layout = f"""# {headers.get('title')}
#### {headers.get("date")}: {research_state.get('date')}

## {headers.get("introduction")}
{research_state.get('introduction')}

## {headers.get("table_of_contents")}
{research_state.get('table_of_contents')}

{custom_sections_text}

{sections_text}

## {headers.get("conclusion")}
{research_state.get('conclusion')}

## {headers.get("references")}
{references}
"""
        return layout

    async def write_report_by_formats(self, layout:str, publish_formats: dict):
        if publish_formats.get("pdf"):
            await write_md_to_pdf(layout, self.output_dir)
        if publish_formats.get("docx"):
            await write_md_to_word(layout, self.output_dir)
        if publish_formats.get("markdown"):
            await write_text_to_md(layout, self.output_dir)

    async def run(self, research_state: dict):
        task = research_state.get("task")
        publish_formats = task.get("publish_formats")
        if self.websocket and self.stream_output:
            await self.stream_output("logs", "publishing", f"Publishing final research report based on retrieved data...", self.websocket)
        else:
            print_agent_output(output="Publishing final research report based on retrieved data...", agent="PUBLISHER")
        final_research_report = await self.publish_research_report(research_state, publish_formats)
        return {"report": final_research_report}

    def _build_required_sections(self, required_sections: list, expert_panel: dict) -> list:
        if not required_sections:
            return []

        idea_candidates = expert_panel.get("idea_candidates", [])
        acceptance_probabilities = expert_panel.get("acceptance_probabilities", [])
        acceptance_map = {item.get("idea_title"): item for item in acceptance_probabilities}

        section_texts = []
        for section in required_sections:
            if section == "Mathematical Formulation":
                content = expert_panel.get("mathematical_formulation", "추가 정보가 필요합니다.")
            elif section == "Proposed Methodology (5 Types)":
                if idea_candidates:
                    content_lines = [
                        f"- **{idea.get('title')}**: {idea.get('summary')} "
                        f"(수학적 증명 가능성: {idea.get('math_proof_feasibility')}, "
                        f"Training-free: {idea.get('training_free')}, "
                        f"Single model: {idea.get('single_model')})"
                        for idea in idea_candidates
                    ]
                    content = "\n".join(content_lines)
                else:
                    content = "추가 정보가 필요합니다."
            elif section == "Expected Novelty & Comparison":
                content = expert_panel.get("gap_analysis", "추가 정보가 필요합니다.")
            elif section == "Estimated Acceptance Probability":
                if acceptance_map:
                    content_lines = []
                    for idea in idea_candidates:
                        idea_title = idea.get("title")
                        acceptance = acceptance_map.get(idea_title, {})
                        content_lines.append(
                            f"- **{idea_title}**: 확률 {acceptance.get('probability')} "
                            f"(근거: {acceptance.get('rationale')})"
                        )
                    content = "\n".join(content_lines)
                else:
                    content = "추가 정보가 필요합니다."
            else:
                content = expert_panel.get("literature_review", "추가 정보가 필요합니다.")

            section_texts.append(f"## {section}\n{content}")

        return section_texts
