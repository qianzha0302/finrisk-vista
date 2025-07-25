import { useState, useCallback } from 'react'
import { supabase } from '@/integrations/supabase/client'

interface PDFChunk {
  text: string
  page: number
  metadata: {
    company: string
  }
}

interface ProcessingProgress {
  stage: 'parsing' | 'chunking' | 'filtering' | 'complete'
  progress: number
  currentPage?: number
  totalPages?: number
  chunksProcessed?: number
  totalChunks?: number
}

interface PDFProcessorResult {
  document_id: string
  company_name: string
  file_name: string
  content: string
  text: string
  paragraphs: PDFChunk[]
  processed: boolean
}

export const usePDFProcessor = () => {
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState<ProcessingProgress>({
    stage: 'parsing',
    progress: 0
  })

  const processDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

  const processPDF = useCallback(async (
    file: File,
    documentId: string,
    companyName: string
  ): Promise<PDFProcessorResult> => {
    setProcessing(true)
    setProgress({ stage: 'parsing', progress: 0 })

    try {
      // Prepare form data for edge function
      const formData = new FormData()
      formData.append('file', file)
      formData.append('document_id', documentId)
      formData.append('company_name', companyName)

      setProgress({ stage: 'parsing', progress: 25 })

      // Call the PDF processor edge function
      const { data, error } = await supabase.functions.invoke('pdf-processor', {
        body: formData,
      })

      if (error) {
        throw new Error(`Edge function error: ${error.message}`)
      }

      setProgress({ stage: 'chunking', progress: 50 })
      await processDelay(500)

      setProgress({ stage: 'filtering', progress: 75 })
      await processDelay(500)

      setProgress({ stage: 'complete', progress: 100 })
      await processDelay(200)

      return data as PDFProcessorResult

    } catch (error) {
      console.error('PDF处理错误:', error)
      throw new Error(`PDF处理失败: ${error instanceof Error ? error.message : '未知错误'}`)
    } finally {
      setProcessing(false)
    }
  }, [])

  return {
    processPDF,
    processing,
    progress
  }
}