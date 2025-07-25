import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import { BarChart3, Plus, Trash2 } from 'lucide-react'

// 预定义的prompt选项，对应prompt registry中的keys
const AVAILABLE_PROMPTS = [
  {
    id: 'risk_classifier',
    name: 'Risk Classification',
    description: 'Comprehensive risk categorization and severity assessment'
  },
  {
    id: 'compliance_audit_v2',
    name: 'Compliance Audit',
    description: 'SEC, FINRA, SOX, and Basel regulatory compliance review'
  },
  {
    id: 'esg_risk_v2',
    name: 'ESG Risk Assessment',
    description: 'Environmental, Social, and Governance risk analysis'
  },
  {
    id: 'financial_health_v3',
    name: 'Financial Health Diagnostic',
    description: 'Multi-dimensional financial health and stability assessment'
  },
  {
    id: 'cybersecurity_risk_v2',
    name: 'Cybersecurity Risk',
    description: 'Data security and cyber threat risk evaluation'
  },
  {
    id: 'operational_resilience_v2',
    name: 'Operational Resilience',
    description: 'Business continuity and operational risk assessment'
  }
]

const RiskAnalysis = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [paragraphs, setParagraphs] = useState([''])
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>(['risk_classifier'])
  const [result, setResult] = useState<any>(null)

  const addParagraph = () => {
    setParagraphs([...paragraphs, ''])
  }

  const removeParagraph = (index: number) => {
    if (paragraphs.length > 1) {
      setParagraphs(paragraphs.filter((_, i) => i !== index))
    }
  }

  const updateParagraph = (index: number, value: string) => {
    const updated = [...paragraphs]
    updated[index] = value
    setParagraphs(updated)
  }

  const togglePrompt = (promptId: string) => {
    setSelectedPrompts(prev => 
      prev.includes(promptId) 
        ? prev.filter(id => id !== promptId)
        : [...prev, promptId]
    )
  }

  const handleAnalysis = async () => {
    const validParagraphs = paragraphs.filter(p => p.trim())

    if (!validParagraphs.length || !selectedPrompts.length) {
      toast.error('Please provide at least one paragraph and select at least one analysis type')
      return
    }

    setLoading(true)
    
    try {
      // 将paragraphs转换为risk_analyzer期望的格式
      const formattedParagraphs = validParagraphs.map((text, index) => ({
        text,
        id: `para_${index}`
      }))

      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          paragraphs: formattedParagraphs,
          prompts: selectedPrompts, // 发送prompt IDs而不是文本
          user_id: user?.id || 'demo-user'
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setResult(data)
        toast.success('Risk analysis completed!')
      } else {
        // Mock result fallback
        setResult({
          results: selectedPrompts.map(promptId => ({
            prompt: promptId,
            analysis: {
              risk_type: 'Market Risk',
              severity: 7,
              confidence: 0.85,
              summary: 'Significant market exposure identified'
            }
          }))
        })
        toast.success('Demo analysis completed (API unavailable)')
      }
    } catch (error) {
      // Mock result fallback
      setResult({
        results: selectedPrompts.map(promptId => ({
          prompt: promptId,
          analysis: {
            risk_type: 'Market Risk',
            severity: 7,
            confidence: 0.85,
            summary: 'Significant market exposure identified'
          }
        }))
      })
      toast.success('Demo analysis completed (API unavailable)')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Risk Analysis</h1>
        <p className="text-muted-foreground">
          Analyze financial documents using advanced risk assessment models
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <BarChart3 className="h-5 w-5" />
              <span>Analysis Input</span>
            </CardTitle>
            <CardDescription>
              Provide document paragraphs and select analysis types
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Document Paragraphs Section */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Document Paragraphs</Label>
                <Button variant="outline" size="sm" onClick={addParagraph}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add
                </Button>
              </div>
              {paragraphs.map((paragraph, index) => (
                <div key={index} className="flex space-x-2">
                  <Textarea
                    value={paragraph}
                    onChange={(e) => updateParagraph(index, e.target.value)}
                    placeholder={`Enter paragraph ${index + 1}...`}
                    rows={3}
                    className="flex-1"
                  />
                  {paragraphs.length > 1 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeParagraph(index)}
                      className="self-start mt-1"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {/* Analysis Types Section */}
            <div className="space-y-4">
              <Label>Analysis Types</Label>
              <div className="grid grid-cols-1 gap-3">
                {AVAILABLE_PROMPTS.map((prompt) => (
                  <div key={prompt.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                    <Checkbox
                      id={prompt.id}
                      checked={selectedPrompts.includes(prompt.id)}
                      onCheckedChange={() => togglePrompt(prompt.id)}
                      className="mt-1"
                    />
                    <div className="grid gap-1.5 leading-none">
                      <label
                        htmlFor={prompt.id}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                      >
                        {prompt.name}
                      </label>
                      <p className="text-xs text-muted-foreground">
                        {prompt.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <Button 
              onClick={handleAnalysis} 
              disabled={loading || selectedPrompts.length === 0}
              className="w-full"
            >
              {loading ? 'Analyzing...' : 'Run Risk Analysis'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Analysis Results</CardTitle>
            <CardDescription>
              Risk analysis output from selected assessment models
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {result.results && result.results.length > 0 ? (
                  result.results.map((item: any, index: number) => {
                    const promptInfo = AVAILABLE_PROMPTS.find(p => p.id === item.prompt)
                    return (
                      <div key={index} className="border rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold">
                            {promptInfo?.name || item.prompt}
                          </h4>
                          {item.analysis?.confidence && (
                            <div className="text-sm text-muted-foreground">
                              Confidence: {Math.round(item.analysis.confidence * 100)}%
                            </div>
                          )}
                        </div>
                        
                        {item.analysis?.risk_type && (
                          <div>
                            <span className="text-sm font-medium">Risk Type: </span>
                            <span className="text-sm text-muted-foreground">
                              {item.analysis.risk_type}
                            </span>
                          </div>
                        )}
                        
                        {item.analysis?.severity && (
                          <div>
                            <span className="text-sm font-medium">Severity: </span>
                            <span className="text-sm text-muted-foreground">
                              {item.analysis.severity}/10
                            </span>
                          </div>
                        )}
                        
                        {item.analysis?.summary && (
                          <p className="text-sm text-muted-foreground">
                            {item.analysis.summary}
                          </p>
                        )}
                        
                        {item.paragraph && (
                          <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
                            <strong>Analyzed text:</strong> {item.paragraph.substring(0, 150)}...
                          </div>
                        )}
                      </div>
                    )
                  })
                ) : (
                  <div className="text-center text-muted-foreground py-4">
                    <p>No analysis results available</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select analysis types and run analysis to see results here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default RiskAnalysis