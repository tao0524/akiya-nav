from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings
from app.models import Document
from app.rag.prompts import DOMAIN_PROMPTS, RAG_TEMPLATE, NO_CONTEXT_TEMPLATE

settings = get_settings()


class RAGPipeline:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key
        )
        self.llm = ChatOpenAI(
            model=settings.chat_model,
            temperature=0.2,
            openai_api_key=settings.openai_api_key
        )

    def search_similar_documents(self, db, query, domain=None, top_k=None):
        if top_k is None:
            top_k = settings.top_k_results

        query_embedding = self.embeddings.embed_query(query)
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        if domain:
            sql = text("""
                SELECT id, content, domain, source, source_page,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM documents
                WHERE domain = :domain
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
            result = db.execute(sql, {
                "embedding": embedding_str,
                "domain": domain,
                "top_k": top_k
            })
        else:
            sql = text("""
                SELECT id, content, domain, source, source_page,
                       1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
                FROM documents
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
            """)
            result = db.execute(sql, {
                "embedding": embedding_str,
                "top_k": top_k
            })

        return result.fetchall()

    def generate_answer(self, question, context_docs, domain=None):
        system_prompt = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["default"])

        if context_docs:
            context_parts = []
            for i, doc in enumerate(context_docs, 1):
                source_info = f"[文書{i}] 出典: {doc.source or '不明'}"
                context_parts.append(f"{source_info}\n{doc.content}")

            context = "\n\n---\n\n".join(context_parts)
            user_message = RAG_TEMPLATE.format(
                context=context,
                question=question
            )
            sources = list(set([doc.source for doc in context_docs if doc.source]))
        else:
            user_message = NO_CONTEXT_TEMPLATE.format(question=question)
            sources = []

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]

        response = self.llm.invoke(messages)

        return {
            "answer": response.content,
            "sources": sources,
            "context_used": len(context_docs)
        }

    def chat(self, db, question, domain=None):
        similar_docs = self.search_similar_documents(
            db=db,
            query=question,
            domain=domain
        )

        result = self.generate_answer(
            question=question,
            context_docs=similar_docs,
            domain=domain
        )

        return result


_pipeline_instance = None


def get_rag_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
