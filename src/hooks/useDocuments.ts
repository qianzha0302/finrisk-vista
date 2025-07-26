import { useState, useEffect } from 'react'
import { supabase } from '@/integrations/supabase/client'
import { useAuth } from '@/hooks/useAuth'

export interface ProcessedDocument {
  id: string
  user_id: string
  document_id: string
  company_name: string
  file_name: string
  content?: string | null
  text_content?: string | null
  paragraphs?: any[] | null
  processed: boolean
  created_at: string
  updated_at: string
}

export const useDocuments = () => {
  const [documents, setDocuments] = useState<ProcessedDocument[]>([])
  const [loading, setLoading] = useState(false)
  const { user } = useAuth()

  const fetchDocuments = async () => {
    if (!user) return

    setLoading(true)
    try {
      const { data, error } = await supabase
        .from('processed_documents')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error

      setDocuments((data || []).map(doc => ({
        ...doc,
        paragraphs: Array.isArray(doc.paragraphs) ? doc.paragraphs : null
      })))
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveDocument = async (documentData: {
    document_id: string
    company_name: string
    file_name: string
    content?: string
    text_content?: string
    paragraphs?: any[]
  }) => {
    if (!user) throw new Error('User not authenticated')

    const { data, error } = await supabase
      .from('processed_documents')
      .upsert({
        user_id: user.id,
        ...documentData,
        processed: true
      })
      .select()
      .single()

    if (error) throw error

    // Refresh documents list
    await fetchDocuments()
    
    return data
  }

  const getDocument = async (documentId: string): Promise<ProcessedDocument | null> => {
    if (!user) return null

    const { data, error } = await supabase
      .from('processed_documents')
      .select('*')
      .eq('document_id', documentId)
      .single()

    if (error) {
      console.error('Error fetching document:', error)
      return null
    }

    return {
      ...data,
      paragraphs: Array.isArray(data.paragraphs) ? data.paragraphs : null
    }
  }

  const deleteDocument = async (documentId: string) => {
    if (!user) throw new Error('User not authenticated')

    const { error } = await supabase
      .from('processed_documents')
      .delete()
      .eq('document_id', documentId)

    if (error) throw error

    // Refresh documents list
    await fetchDocuments()
  }

  useEffect(() => {
    if (user) {
      fetchDocuments()
    }
  }, [user])

  return {
    documents,
    loading,
    saveDocument,
    getDocument,
    deleteDocument,
    fetchDocuments
  }
}