import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { BarChart3, Network, TrendingUp, Eye } from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts'

interface RiskVisualizationProps {
  analysisData: any
  companyName?: string
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#8dd1e1', '#d084d0']

const RiskVisualization = ({ analysisData, companyName = "Company" }: RiskVisualizationProps) => {
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [loadingVisualization, setLoadingVisualization] = useState(false)
  const [graphData, setGraphData] = useState<any>(null)
  const [visualizationData, setVisualizationData] = useState<any>(null)

  // 从分析结果中提取图表数据
  const getChartData = () => {
    if (!analysisData?.results) return {
      riskTypes: [],
      severityData: []
    }
    
    const riskCounts: { [key: string]: number } = {}
    const severityData: { name: string; severity: number; count: number }[] = []
    
    analysisData.results.forEach((result: any) => {
      const riskType = result.analysis?.risk_type || 'Unknown'
      const severity = result.analysis?.severity || 0
      
      riskCounts[riskType] = (riskCounts[riskType] || 0) + 1
      severityData.push({
        name: riskType,
        severity: severity,
        count: 1
      })
    })

    return {
      riskTypes: Object.entries(riskCounts).map(([name, value]) => ({
        name,
        value,
        count: value
      })),
      severityData
    }
  }

  const { riskTypes, severityData } = getChartData()

  const generateRiskGraph = async () => {
    setLoadingGraph(true)
    try {
      const response = await fetch('http://localhost:8000/generate-graph', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_data: analysisData,
          company_name: companyName,
          graph_type: 'network'
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setGraphData(data)
      } else {
        // Mock data fallback
        setGraphData({
          graph_html: '<div>Mock Risk Network Graph</div>',
          nodes_count: 15,
          edges_count: 22
        })
      }
    } catch (error) {
      console.error('Error generating graph:', error)
      // Mock data fallback
      setGraphData({
        graph_html: '<div>Mock Risk Network Graph</div>',
        nodes_count: 15,
        edges_count: 22
      })
    } finally {
      setLoadingGraph(false)
    }
  }

  const generateVisualization = async (type: string) => {
    setLoadingVisualization(true)
    try {
      // 模拟数据转换为后端期望的格式
      const dfsData = {
        "2024": analysisData.results?.map((result: any, index: number) => ({
          risk_type_1: result.analysis?.risk_type || 'Unknown',
          severity_1: result.analysis?.severity || 0,
          Paragraph: `Analysis paragraph ${index + 1}`
        })) || []
      }

      const response = await fetch('http://localhost:8000/generate-visualization', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          dfs_by_year: dfsData,
          visualization_type: type
        }),
      })

      if (response.ok) {
        const data = await response.json()
        setVisualizationData(data)
      } else {
        // Mock visualization data
        setVisualizationData({
          type: type,
          path: `/mock-${type}.html`,
          mock: true
        })
      }
    } catch (error) {
      console.error('Error generating visualization:', error)
      setVisualizationData({
        type: type,
        path: `/mock-${type}.html`,
        mock: true
      })
    } finally {
      setLoadingVisualization(false)
    }
  }

  if (!analysisData?.results?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Risk Visualization</span>
          </CardTitle>
          <CardDescription>
            Visual analysis will appear here after running risk assessment
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center text-muted-foreground py-8">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No analysis data available for visualization</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <BarChart3 className="h-5 w-5" />
          <span>Risk Visualization</span>
        </CardTitle>
        <CardDescription>
          Interactive charts and graphs of your risk analysis results
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="charts" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="charts">Charts</TabsTrigger>
            <TabsTrigger value="network">Network Graph</TabsTrigger>
            <TabsTrigger value="advanced">Advanced</TabsTrigger>
          </TabsList>
          
          <TabsContent value="charts" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Risk Types Distribution */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Risk Types Distribution</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={riskTypes}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {riskTypes.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Severity Levels */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Risk Severity Levels</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={severityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="severity" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Summary Statistics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-primary">
                  {analysisData.results.length}
                </div>
                <div className="text-sm text-muted-foreground">Total Risks</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-destructive">
                  {severityData.filter(d => d.severity >= 7).length}
                </div>
                <div className="text-sm text-muted-foreground">High Severity</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-orange-500">
                  {severityData.filter(d => d.severity >= 4 && d.severity < 7).length}
                </div>
                <div className="text-sm text-muted-foreground">Medium Severity</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-500">
                  {severityData.filter(d => d.severity < 4).length}
                </div>
                <div className="text-sm text-muted-foreground">Low Severity</div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="network" className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium">Risk Network Graph</h4>
                <p className="text-xs text-muted-foreground">
                  Interactive network visualization of risk relationships
                </p>
              </div>
              <Button 
                onClick={generateRiskGraph}
                disabled={loadingGraph}
                size="sm"
              >
                <Network className="h-4 w-4 mr-2" />
                {loadingGraph ? 'Generating...' : 'Generate Graph'}
              </Button>
            </div>
            
            {graphData ? (
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex space-x-4">
                    <Badge variant="secondary">
                      Nodes: {graphData.nodes_count}
                    </Badge>
                    <Badge variant="secondary">
                      Connections: {graphData.edges_count}
                    </Badge>
                  </div>
                  <Button variant="outline" size="sm">
                    <Eye className="h-4 w-4 mr-2" />
                    View Full Graph
                  </Button>
                </div>
                <div className="bg-muted rounded p-8 text-center">
                  <Network className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Interactive risk network graph would be displayed here
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Graph path: {graphData.graph_path || 'Mock graph'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-8">
                <Network className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Click "Generate Graph" to create risk network visualization</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6">
            <div className="space-y-4">
              <h4 className="text-sm font-medium">Advanced Visualizations</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button 
                  variant="outline" 
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={() => generateVisualization('trend')}
                  disabled={loadingVisualization}
                >
                  <TrendingUp className="h-8 w-8" />
                  <div className="text-center">
                    <div className="font-medium">Trend Analysis</div>
                    <div className="text-xs text-muted-foreground">Risk trends over time</div>
                  </div>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={() => generateVisualization('heatmap')}
                  disabled={loadingVisualization}
                >
                  <BarChart3 className="h-8 w-8" />
                  <div className="text-center">
                    <div className="font-medium">Risk Heatmap</div>
                    <div className="text-xs text-muted-foreground">Risk type vs severity</div>
                  </div>
                </Button>
                
                <Button 
                  variant="outline" 
                  className="h-auto p-4 flex flex-col items-center space-y-2"
                  onClick={() => generateVisualization('wordcloud')}
                  disabled={loadingVisualization}
                >
                  <Eye className="h-8 w-8" />
                  <div className="text-center">
                    <div className="font-medium">Word Cloud</div>
                    <div className="text-xs text-muted-foreground">Key terms visualization</div>
                  </div>
                </Button>
              </div>
            </div>

            {visualizationData && (
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h5 className="font-medium capitalize">{visualizationData.type} Visualization</h5>
                    <p className="text-xs text-muted-foreground">
                      Generated visualization: {visualizationData.path}
                    </p>
                  </div>
                  {visualizationData.mock && (
                    <Badge variant="outline">Demo Mode</Badge>
                  )}
                </div>
                <div className="bg-muted rounded p-8 text-center">
                  <BarChart3 className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    {visualizationData.type} visualization would be displayed here
                  </p>
                </div>
              </div>
            )}
            
            {loadingVisualization && (
              <div className="text-center text-muted-foreground py-8">
                <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
                <p>Generating visualization...</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

export default RiskVisualization