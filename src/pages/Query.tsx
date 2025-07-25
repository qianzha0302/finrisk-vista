import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import { Search, MessageSquare } from 'lucide-react'

const Query = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [question, setQuestion] = useState('')
  const [documentId, setDocumentId] = useState('')
  const [answer, setAnswer] = useState('')
  const [queryHistory, setQueryHistory] = useState<Array<{question: string, answer: string}>>([])

  const handleQuery = async () => {
    if (!question.trim()) {
      toast.error('Please enter a question')
      return
    }

    setLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          document_id: documentId || 'default_doc',
          user_id: user?.id || 'demo-user'
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setAnswer(data.answer || data.response || 'Analysis completed successfully')
        setQueryHistory(prev => [...prev, { question: question.trim(), answer: data.answer || data.response || 'Analysis completed' }])
        toast.success('Query processed successfully!')
      } else {
        // Mock response fallback
        const mockAnswer = `Based on the financial analysis, here are the key insights regarding "${question}": 
        
The risk assessment indicates moderate exposure with several factors to consider. Key recommendations include implementing stronger controls and monitoring mechanisms.`
        
        setAnswer(mockAnswer)
        setQueryHistory(prev => [...prev, { question: question.trim(), answer: mockAnswer }])
        toast.success('Demo query processed (API unavailable)')
      }
    } catch (error) {
      // Mock response fallback
      const mockAnswer = `Based on the financial analysis, here are the key insights regarding "${question}": 
      
The risk assessment indicates moderate exposure with several factors to consider. Key recommendations include implementing stronger controls and monitoring mechanisms.`
      
      setAnswer(mockAnswer)
      setQueryHistory(prev => [...prev, { question: question.trim(), answer: mockAnswer }])
      toast.success('Demo query processed (API unavailable)')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleQuery()
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Query Documents</h1>
        <p className="text-muted-foreground">
          Ask questions about your uploaded financial documents
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Search className="h-5 w-5" />
                <span>Ask a Question</span>
              </CardTitle>
              <CardDescription>
                Query your financial documents using natural language
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="document_id">Document ID (Optional)</Label>
                <Input
                  id="document_id"
                  value={documentId}
                  onChange={(e) => setDocumentId(e.target.value)}
                  placeholder="Enter specific document ID or leave blank for all documents"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="question">Your Question</Label>
                <div className="flex space-x-2">
                  <Input
                    id="question"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="e.g., What are the main risk factors in the latest financial report?"
                    className="flex-1"
                  />
                  <Button onClick={handleQuery} disabled={loading}>
                    {loading ? 'Searching...' : 'Ask'}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {answer && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="h-5 w-5" />
                  <span>Answer</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="prose prose-sm max-w-none">
                  <p className="text-foreground whitespace-pre-wrap">{answer}</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Query History</CardTitle>
              <CardDescription>Your recent questions and answers</CardDescription>
            </CardHeader>
            <CardContent>
              {queryHistory.length > 0 ? (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {queryHistory.slice().reverse().map((item, index) => (
                    <div key={index} className="border-b border-border pb-3 last:border-b-0">
                      <p className="text-sm font-medium text-foreground mb-1">
                        Q: {item.question}
                      </p>
                      <p className="text-xs text-muted-foreground line-clamp-3">
                        A: {item.answer}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No queries yet. Ask your first question above.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sample Questions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[
                  "What are the main risk factors?",
                  "Summarize the financial performance",
                  "What are the key recommendations?",
                  "Identify potential compliance issues",
                  "What is the overall risk assessment?"
                ].map((sample, index) => (
                  <Button
                    key={index}
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-left h-auto p-2"
                    onClick={() => setQuestion(sample)}
                  >
                    <span className="text-xs">{sample}</span>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Query