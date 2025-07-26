import { useState, useCallback } from 'react'
import { supabase } from '@/integrations/supabase/client'

export interface RAGQueryResult {
  query: string
  answer: string
  confidence_score: number
  relevant_paragraphs: Array<{
    content: string
    metadata: any
    relevance_score: number
  }>
  document_id: string
  processing_time: number
  documents_retrieved: number
}

export interface ConversationMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp?: number
}

export const useRAGQuery = () => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conversation, setConversation] = useState<ConversationMessage[]>([])

  const queryDocument = useCallback(async (
    documentId: string,
    question: string,
    includeHistory: boolean = true
  ): Promise<RAGQueryResult | null> => {
    if (!documentId || !question.trim()) {
      setError('Document ID and question are required')
      return null
    }

    setLoading(true)
    setError(null)

    try {
      console.log(`🔍 Starting RAG query for document: ${documentId}`)
      console.log(`❓ Question: ${question}`)

      // Prepare conversation history
      const conversationHistory = includeHistory ? conversation.slice(-6) : [] // Last 6 messages

      // Call the RAG query edge function
      const { data, error: functionError } = await supabase.functions.invoke('rag-query', {
        body: {
          document_id: documentId,
          question: question.trim(),
          conversation_history: conversationHistory
        }
      })

      if (functionError) {
        console.error('RAG query function error:', functionError)
        throw new Error(`Query failed: ${functionError.message}`)
      }

      if (!data) {
        throw new Error('No response received from RAG service')
      }

      console.log(`✅ RAG query completed:`, data)

      // Update conversation history
      const newMessages: ConversationMessage[] = [
        { role: 'user', content: question, timestamp: Date.now() },
        { role: 'assistant', content: data.answer, timestamp: Date.now() }
      ]

      setConversation(prev => [...prev, ...newMessages])

      return data as RAGQueryResult

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      console.error('RAG query error:', errorMessage)
      setError(errorMessage)
      return null
    } finally {
      setLoading(false)
    }
  }, [conversation])

  const clearConversation = useCallback(() => {
    setConversation([])
    setError(null)
  }, [])

  const removeLastExchange = useCallback(() => {
    setConversation(prev => prev.slice(0, -2)) // Remove last user + assistant pair
  }, [])

  const queryWithFollowUp = useCallback(async (
    documentId: string,
    question: string
  ): Promise<RAGQueryResult | null> => {
    return queryDocument(documentId, question, true)
  }, [queryDocument])

  const queryFresh = useCallback(async (
    documentId: string,
    question: string
  ): Promise<RAGQueryResult | null> => {
    return queryDocument(documentId, question, false)
  }, [queryDocument])

  // Batch query multiple questions
  const batchQuery = useCallback(async (
    documentId: string,
    questions: string[]
  ): Promise<Array<RAGQueryResult | null>> => {
    const results: Array<RAGQueryResult | null> = []
    
    for (const question of questions) {
      try {
        const result = await queryDocument(documentId, question, false)
        results.push(result)
        
        // Small delay between queries to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (err) {
        console.error(`Batch query failed for question: ${question}`, err)
        results.push(null)
      }
    }
    
    return results
  }, [queryDocument])

  return {
    queryDocument,
    queryWithFollowUp,
    queryFresh,
    batchQuery,
    clearConversation,
    removeLastExchange,
    loading,
    error,
    conversation,
    hasConversation: conversation.length > 0
  }
}