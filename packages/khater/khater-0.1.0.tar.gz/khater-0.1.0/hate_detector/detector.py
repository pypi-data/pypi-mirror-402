import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class HateSpeechDetector:
    def __init__(self, api_key, excluded_words=None):
        """
        초기화 단계: 기존 main.py의 4, 5, 6번 과정(지식 베이스 및 모델 설정)이 여기로 옵니다.
        """
        self.api_key = api_key
        self.excluded_words = excluded_words or []
        
        # 4. 혐오/모욕 지식 베이스
        self.knowledge_base = [
            "숫자 삽입 우회: '씨12발', '씨329...발' 처럼 중간에 숫자를 넣은 것은 모두 심한 욕설임.",
            "지능적 비꼬기: '씨12발스러운 분위기'처럼 정중한 말투에 욕설 형용사를 섞는 행위.",
            "자음/모음 분리: 'ㅅㅣㅂㅏㄹ', 'ㅆㅂ' 등 초성/분리형 욕설 탐지.",
            "혐오 표현: 특정 집단을 벌레(충)에 비유하거나 지역/성별을 비하하는 발언."
        ]
        
        # 5. 벡터 DB 구축 (수동 RAG를 위한 준비)
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        self.vectorstore = FAISS.from_texts(self.knowledge_base, self.embeddings)
        
        # 6. LLM 모델 설정 (비용 절감을 위해 gpt-4o-mini 사용 가능)
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0, openai_api_key=self.api_key)

    def detect(self, user_text):
        """
        실행 단계: 기존 main.py의 7번 루프 안의 '수동 RAG 로직'이 여기로 옵니다.
        """
        try:
            # 1단계: 유사 검색
            docs = self.vectorstore.similarity_search(user_text, k=2)
            context = "\n".join([d.page_content for d in docs])
            
            # 2단계: 프롬프트 구성 (사용자가 입력한 excluded_words 반영)
            system_instruction = (
                "당신은 커뮤니티 언어 정화 전문가입니다. 제공된 참고 지식을 바탕으로 분석하세요.\n\n"
                "--- 분석 규칙 ---\n"
                f"1. **문맥적 모욕**: '씨12발스러운'처럼 비꼬는 경우 판정하세요.\n"
                f"2. **강력한 우회어 탐지**: 숫자/기호 섞인 욕설 원형 유추.\n"
                f"3. **예외 처리**: {self.excluded_words} 리스트의 단어는 허용하세요.\n\n"
                "--- 출력 형식 ---\n"
                "- 판정: [결과]\n- 공격성 점수: [0~100]\n- 분석 이유: (설명)"
            )
            
            messages = [
                ("system", f"{system_instruction}\n\n참고 지식:\n{context}"),
                ("human", user_text)
            ]
            
            # 3단계: 호출
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"분석 중 오류 발생: {e}"