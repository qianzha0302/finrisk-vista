import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/hooks/useAuth'
import toast from 'react-hot-toast'
import { BarChart3, Plus, Trash2 } from 'lucide-react'

const RiskAnalysis = () => {
  const { user } = useAuth()
  const [loading, setLoading] = useState(false)
  const [paragraphs, setParagraphs] = useState([''])
  const [prompts, setPrompts] = useState(['Analyze the financial risk factors'])
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

  const addPrompt = () => {
    setPrompts([...prompts, ''])
  }

  const removePrompt = (index: number) => {
    if (prompts.length > 1) {
      setPrompts(prompts.filter((_, i) => i !== index))
    }
  }

  const updatePrompt = (index: number, value: string) => {
    const updated = [...prompts]
    updated[index] = value
    setPrompts(updated)
  }

  const handleAnalysis = async () => {
    const validParagraphs = paragraphs.filter(p => p.trim())
    const validPrompts = prompts.filter(p => p.trim())

    if (!validParagraphs.length || !validPrompts.length) {
      toast.error('Please provide at least one paragraph and one prompt')
      return
    }

    setLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          paragraphs: validParagraphs,
          prompts: validPrompts,
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
          risk_score: Math.floor(Math.random() * 100),
          risk_factors: [
            'High debt-to-equity ratio',
            'Declining revenue trends',
            'Market volatility exposure'
          ],
          recommendations: [
            'Implement debt reduction strategy',
            'Diversify revenue streams',
            'Enhance risk monitoring'
          ],
          analysis_summary: 'The financial risk analysis reveals moderate to high risk exposure across multiple factors.'
        })
        toast.success('Demo analysis completed (API unavailable)')
      }
    } catch (error) {
      // Mock result fallback
      setResult({
        risk_score: Math.floor(Math.random() * 100),
        risk_factors: [
          'High debt-to-equity ratio',
          'Declining revenue trends',
          'Market volatility exposure'
        ],
        recommendations: [
          'Implement debt reduction strategy',
          'Diversify revenue streams',
          'Enhance risk monitoring'
        ],
        analysis_summary: 'The financial risk analysis reveals moderate to high risk exposure across multiple factors.'
      })
      toast.success('Demo analysis completed (API unavailable)')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Risk Analysis</h1>
        <p className="text-muted-foreground">
          Analyze financial documents and data for risk assessment
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
              Provide paragraphs and prompts for risk analysis
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
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

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Label>Analysis Prompts</Label>
                <Button variant="outline" size="sm" onClick={addPrompt}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add
                </Button>
              </div>
              {prompts.map((prompt, index) => (
                <div key={index} className="flex space-x-2">
                  <Textarea
                    value={prompt}
                    onChange={(e) => updatePrompt(index, e.target.value)}
                    placeholder={`Enter analysis prompt ${index + 1}...`}
                    rows={2}
                    className="flex-1"
                  />
                  {prompts.length > 1 && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removePrompt(index)}
                      className="self-start mt-1"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            <Button 
              onClick={handleAnalysis} 
              disabled={loading}
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
              Risk analysis output and recommendations
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-primary">
                    {result.risk_score}%
                  </div>
                  <p className="text-sm text-muted-foreground">Risk Score</p>
                </div>

                {result.analysis_summary && (
                  <div>
                    <h4 className="font-semibold mb-2">Summary</h4>
                    <p className="text-sm text-muted-foreground">
                      {result.analysis_summary}
                    </p>
                  </div>
                )}

                {result.risk_factors && (
                  <div>
                    <h4 className="font-semibold mb-2">Risk Factors</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                      {result.risk_factors.map((factor: string, index: number) => (
                        <li key={index}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.recommendations && (
                  <div>
                    <h4 className="font-semibold mb-2">Recommendations</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
                      {result.recommendations.map((rec: string, index: number) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Run analysis to see results here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default RiskAnalysis