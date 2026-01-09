from typing import Dict, List

from .utils.llms import call_model
from .utils.views import print_agent_output


class ExpertPanelAgent:
    def __init__(self, websocket=None, stream_output=None, headers=None):
        self.websocket = websocket
        self.stream_output = stream_output
        self.headers = headers or {}

    async def run(self, research_state: Dict[str, any]) -> Dict[str, any]:
        task = research_state.get("task", {})
        initial_research = research_state.get("initial_research")
        personas = task.get("agent_personas", [])
        max_followup_rounds = task.get("max_followup_rounds", 1)
        followup_rounds = research_state.get("followup_rounds", 0)

        prompt = self._create_panel_prompt(task.get("query"), initial_research, personas)
        if self.websocket and self.stream_output:
            await self.stream_output(
                "logs",
                "expert_panel",
                "전문가 페르소나 토론을 통해 연구 아이디어를 정리 중입니다...",
                self.websocket,
            )
        else:
            print_agent_output(
                "Running expert panel debate for research ideas...",
                agent="EDITOR",
            )

        panel_output = await call_model(
            prompt=prompt,
            model=task.get("model"),
            response_format="json",
        )

        needs_more_research = bool(panel_output.get("needs_more_research"))
        followup_query = panel_output.get("followup_query")

        if needs_more_research and followup_rounds >= max_followup_rounds:
            needs_more_research = False
            followup_query = None

        updated_task = dict(task)
        if followup_query:
            updated_task["followup_query"] = followup_query

        return {
            "task": updated_task,
            "expert_panel": panel_output,
            "needs_more_research": needs_more_research,
            "followup_rounds": followup_rounds + (1 if needs_more_research else 0),
        }

    def _create_panel_prompt(
        self,
        query: str,
        initial_research: str,
        personas: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        personas_text = "\n".join(
            f"- {persona.get('name')}: {persona.get('role')} | {persona.get('persona')}"
            for persona in personas
        )
        return [
            {
                "role": "system",
                "content": "당신은 멀티 에이전트 연구 팀의 조율자입니다. "
                "주어진 페르소나를 활용해 공개 가능한 토론 요약과 연구 아이디어를 정리하세요.",
            },
            {
                "role": "user",
                "content": f"""연구 주제: {query}

초기 리서치 요약:
{initial_research}

전문가 페르소나:
{personas_text}

요구사항:
1) 문헌 조사 요약(Literature Review)과 Gap Analysis를 한국어로 작성.
2) 5개의 연구 아이디어를 도출하고 각 아이디어마다 (a) 수학적 증명 가능성, (b) 비학습(Training-free) 여부,
   (c) 단일 모델 적용 가능성을 명시.
3) 각 아이디어의 Top-tier 학회 Accept 확률(0~1)을 이론적 근거와 함께 제시.
4) 추가 조사가 필요하면 needs_more_research=true로 표기하고 followup_query에 조사 키워드를 작성.
5) 체인 오브 쏘트는 제공하지 말고, 공개 가능한 요약만 작성.

출력은 아래 JSON 형식만 반환:
{{
  "discussion_summary": [
    {{"name": "Persona Name", "key_points": ["요약 포인트1", "요약 포인트2"]}}
  ],
  "literature_review": "...",
  "gap_analysis": "...",
  "mathematical_formulation": "...",
  "idea_candidates": [
    {{
      "title": "...",
      "summary": "...",
      "math_proof_feasibility": "...",
      "training_free": true,
      "single_model": true
    }}
  ],
  "acceptance_probabilities": [
    {{
      "idea_title": "...",
      "probability": 0.65,
      "rationale": "..."
    }}
  ],
  "needs_more_research": false,
  "followup_query": null
}}
""",
            },
        ]
