# Enhanced Reporting Implementation Plan

## Overview
Transform the current basic reporting into comprehensive, multi-faceted analysis with visualizations, deep LLM insights, and actionable recommendations.

## Key Features

### 1. Multi-Faceted Analysis
- **Dimension-level**: Overall scores and insights per dimension
- **Category-level**: Aggregated analysis by question category
- **Process-level**: Aggregated analysis by process
- **Lifecycle Stage-level**: Aggregated analysis by lifecycle stage

### 2. Visualizations
- **Radar Chart**: Multi-dimensional scoring across all dimensions
- **Bar Charts**: Category/Process/Lifecycle comparisons
- **Data Tables**: Aggregated metrics with drill-down capability
- **Word Cloud**: Comment frequency and sentiment visualization

### 3. LLM-Powered Analysis
- Deep strategic observations per dimension
- Actionable recommendations
- Sentiment analysis of comments
- Cross-facet insights

---

## Implementation Phases

### Phase 1: Backend Data Aggregation

#### File: `backend/app/routers/reports.py`

**New Functions Needed:**

```python
def aggregate_by_category(responses, questions):
    """Aggregate scores by category"""
    category_data = {}
    for category in set(q.category for q in questions if q.category):
        scores = [r.score for r in responses
                 if r.question.category == category and r.score != 'NA']
        category_data[category] = {
            'avg_score': mean(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'count': len(scores),
            'comments': [r.comment for r in responses
                        if r.question.category == category and r.comment]
        }
    return category_data

def aggregate_by_process(responses, questions):
    """Aggregate scores by process"""
    # Similar to category aggregation

def aggregate_by_lifecycle_stage(responses, questions):
    """Aggregate scores by lifecycle stage"""
    # Similar to category aggregation

def analyze_comments(comments, llm_config):
    """Use LLM for sentiment analysis and key themes"""
    prompt = f"""
    Analyze these survey comments for:
    1. Overall sentiment (positive/negative/neutral percentages)
    2. Key themes and concerns
    3. Most frequently mentioned topics

    Comments:
    {comments}
    """
    # Call LLM service
    return sentiment_analysis
```

**Enhanced Endpoint Response Structure:**

```json
{
  "dimension": "Data Privacy & Compliance",

  "overall_metrics": {
    "avg_score": 7.5,
    "min_score": 3.0,
    "max_score": 10.0,
    "total_responses": 150,
    "response_rate": "88%"
  },

  "category_analysis": {
    "Policy": {
      "avg_score": 8.2,
      "scores": [7, 8, 9, 10, ...],
      "comments": ["...", "..."],
      "llm_analysis": "Strategic insights..."
    },
    "Technology": { ... }
  },

  "process_analysis": {
    "Assessment": { ... },
    "Implementation": { ... }
  },

  "lifecycle_analysis": {
    "Planning": { ... },
    "Execution": { ... }
  },

  "comment_insights": {
    "total_comments": 45,
    "sentiment": {
      "positive": 60,
      "neutral": 30,
      "negative": 10
    },
    "word_frequency": {
      "compliance": 25,
      "privacy": 20,
      ...
    },
    "key_themes": ["...", "..."],
    "llm_summary": "Overall comment analysis..."
  },

  "dimension_llm_analysis": {
    "strategic_observations": "...",
    "strengths": ["...", "..."],
    "gaps": ["...", "..."],
    "recommendations": ["...", "..."]
  }
}
```

### Phase 2: Enhanced LLM Prompts

#### File: `backend/app/llm_service.py`

**New Analysis Methods:**

```python
@staticmethod
async def generate_deep_dimension_analysis(config, dimension_data):
    """Generate comprehensive dimension analysis"""
    prompt = f"""
    As a data governance expert, provide a comprehensive analysis of {dimension_data['dimension']}.

    METRICS:
    - Average Score: {dimension_data['avg_score']}/10
    - Response Rate: {dimension_data['response_rate']}
    - Score Range: {dimension_data['min_score']} - {dimension_data['max_score']}

    CATEGORY BREAKDOWN:
    {format_category_scores(dimension_data['categories'])}

    PROCESS BREAKDOWN:
    {format_process_scores(dimension_data['processes'])}

    LIFECYCLE BREAKDOWN:
    {format_lifecycle_scores(dimension_data['lifecycle_stages'])}

    Provide:

    ## Strategic Observations
    - What do these scores indicate about organizational maturity?
    - Which areas show strength vs weakness?
    - Are there concerning patterns?

    ## Category Analysis
    - Compare category performance
    - Identify highest/lowest performing categories
    - Explain why certain categories may lag

    ## Process Analysis
    - Which processes need attention?
    - Are processes balanced or uneven?

    ## Lifecycle Analysis
    - Which lifecycle stages are problematic?
    - Is there a progression issue?

    ## Actionable Recommendations
    Provide 5-7 specific, prioritized actions with:
    - Quick wins (< 3 months)
    - Medium-term improvements (3-6 months)
    - Strategic initiatives (6-12 months)

    Format in markdown with clear headers and bullet points.
    """

@staticmethod
async def analyze_facet(config, facet_type, facet_data):
    """Analyze specific facet (category/process/lifecycle)"""
    prompt = f"""
    Analyze this {facet_type} facet of data governance:

    {facet_type.upper()}: {facet_data['name']}
    Average Score: {facet_data['avg_score']}/10

    Questions in this {facet_type}:
    {format_questions(facet_data['questions'])}

    Comments:
    {format_comments(facet_data['comments'])}

    Provide:
    1. Performance Assessment
    2. Root Cause Analysis (why this score?)
    3. Specific Recommendations
    4. Success Metrics to track improvement

    Format in markdown.
    """

@staticmethod
async def analyze_comments_sentiment(config, comments):
    """LLM-based sentiment and thematic analysis"""
    prompt = f"""
    Analyze these survey comments:

    {format_comments(comments)}

    Provide:

    ## Sentiment Analysis
    - Positive comments: X%
    - Neutral comments: Y%
    - Negative comments: Z%

    ## Key Themes
    List the 5-7 most common themes

    ## Top Concerns
    What are respondents most worried about?

    ## Positive Highlights
    What are they happy about?

    ## Word Cloud Data
    Provide top 20 words by frequency in JSON format

    Format in markdown with JSON at the end.
    """
```

### Phase 3: Frontend Components

#### New Components to Create:

**1. `/frontend/src/components/RadarChart.jsx`**
```jsx
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';

export default function DimensionRadarChart({ data }) {
  // data = [{ dimension: "Privacy", score: 7.5 }, ...]
  return (
    <RadarChart width={600} height={400} data={data}>
      <PolarGrid />
      <PolarAngleAxis dataKey="dimension" />
      <PolarRadiusAxis domain={[0, 10]} />
      <Radar name="Score" dataKey="score" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
    </RadarChart>
  );
}
```

**2. `/frontend/src/components/FacetBarChart.jsx`**
```jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export default function FacetBarChart({ data, facetType }) {
  // data = [{ name: "Category A", score: 7.5, responses: 25 }, ...]
  return (
    <BarChart width={800} height={400} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="name" />
      <YAxis domain={[0, 10]} />
      <Tooltip />
      <Legend />
      <Bar dataKey="score" fill="#8884d8" />
    </BarChart>
  );
}
```

**3. `/frontend/src/components/CommentWordCloud.jsx`**
```jsx
import ReactWordcloud from 'react-wordcloud';

export default function CommentWordCloud({ words }) {
  // words = [{ text: "privacy", value: 25 }, ...]
  return (
    <div style={{ height: 400, width: '100%' }}>
      <ReactWordcloud words={words} />
    </div>
  );
}
```

**4. `/frontend/src/components/MetricsTable.jsx`**
```jsx
export default function MetricsTable({ data }) {
  return (
    <table className="min-w-full divide-y divide-gray-200">
      <thead className="bg-gray-50">
        <tr>
          <th>Facet</th>
          <th>Avg Score</th>
          <th>Min</th>
          <th>Max</th>
          <th>Responses</th>
        </tr>
      </thead>
      <tbody>
        {data.map(row => (
          <tr key={row.name}>
            <td>{row.name}</td>
            <td>{row.avg.toFixed(2)}</td>
            <td>{row.min}</td>
            <td>{row.max}</td>
            <td>{row.count}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### Phase 4: Enhanced Report Page Structure

**File: `/frontend/src/pages/DimensionReport.jsx`** (New comprehensive view)

```jsx
export default function DimensionReport() {
  return (
    <div className="space-y-8">
      {/* Section 1: Overview */}
      <section>
        <h2>Dimension Overview</h2>
        <div className="grid grid-cols-4 gap-4">
          <MetricCard title="Avg Score" value="7.5" />
          <MetricCard title="Response Rate" value="88%" />
          <MetricCard title="Total Responses" value="150" />
          <MetricCard title="Comments" value="45" />
        </div>
      </section>

      {/* Section 2: Dimension-Level Analysis */}
      <section>
        <h2>Dimension Analysis</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3>Score Distribution</h3>
            <BarChart data={scoreDistribution} />
          </div>
          <div>
            <h3>Questions Summary</h3>
            <MetricsTable data={questionMetrics} />
          </div>
        </div>
        <div className="mt-4">
          <h3>Strategic Insights</h3>
          <LLMAnalysis content={dimensionAnalysis} />
        </div>
      </section>

      {/* Section 3: Category Analysis */}
      <section>
        <h2>Category Analysis</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3>Category Scores</h3>
            <FacetBarChart data={categoryScores} facetType="category" />
            <p className="text-sm mt-2">
              <strong>Interpretation:</strong> This chart shows...
            </p>
          </div>
          <div>
            <h3>Category Metrics</h3>
            <MetricsTable data={categoryMetrics} />
          </div>
        </div>
        <div className="mt-4">
          <h3>Category Insights</h3>
          <LLMAnalysis content={categoryAnalysis} />
        </div>
      </section>

      {/* Section 4: Process Analysis */}
      <section>
        <h2>Process Analysis</h2>
        {/* Similar structure to Category */}
      </section>

      {/* Section 5: Lifecycle Analysis */}
      <section>
        <h2>Lifecycle Stage Analysis</h2>
        {/* Similar structure to Category */}
      </section>

      {/* Section 6: Comment Analysis */}
      <section>
        <h2>Comment Analysis</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h3>Sentiment Distribution</h3>
            <PieChart data={sentimentData} />
          </div>
          <div>
            <h3>Word Frequency</h3>
            <CommentWordCloud words={wordFrequency} />
          </div>
        </div>
        <div className="mt-4">
          <h3>Key Themes</h3>
          <LLMAnalysis content={commentAnalysis} />
        </div>
      </section>

      {/* Section 7: Radar Chart - Cross-Dimension View */}
      <section>
        <h2>Multi-Dimensional Overview</h2>
        <RadarChart data={allDimensions} />
        <p className="mt-4">
          <strong>Interpretation:</strong> This radar chart shows relative performance across all dimensions...
        </p>
      </section>
    </div>
  );
}
```

---

## Implementation Checklist

### Backend Work
- [ ] Create data aggregation functions for category/process/lifecycle
- [ ] Enhance reports endpoint with multi-faceted data
- [ ] Implement comment sentiment analysis with LLM
- [ ] Create word frequency calculator
- [ ] Add deep analysis LLM prompts
- [ ] Add facet-specific LLM analysis
- [ ] Test aggregation logic with sample data

### Frontend Work
- [ ] Install dependencies (`npm install` in frontend)
- [ ] Create RadarChart component
- [ ] Create FacetBarChart component
- [ ] Create MetricsTable component
- [ ] Create CommentWordCloud component
- [ ] Create LLMAnalysis display component
- [ ] Build enhanced DimensionReport page
- [ ] Add data interpretation text for each chart
- [ ] Style all components consistently
- [ ] Add loading states and error handling

### LLM Integration
- [ ] Test dimension-level prompts for quality
- [ ] Test category-level prompts
- [ ] Test process-level prompts
- [ ] Test lifecycle-level prompts
- [ ] Test comment sentiment prompts
- [ ] Refine prompts based on output quality
- [ ] Add prompt templates for consistency

### Testing & Refinement
- [ ] Test with real survey data
- [ ] Verify calculations are correct
- [ ] Ensure LLM responses are actionable
- [ ] Check mobile responsiveness
- [ ] Validate chart rendering
- [ ] Test with different data volumes
- [ ] Performance optimization if needed

---

## Estimated Timeline

- **Phase 1** (Backend Aggregation): 2-3 hours
- **Phase 2** (LLM Prompts): 2-3 hours
- **Phase 3** (Frontend Components): 3-4 hours
- **Phase 4** (Report Page Assembly): 2-3 hours
- **Testing & Refinement**: 2-3 hours

**Total**: ~12-16 hours of development work

---

## Next Steps

1. Review this plan and confirm the approach
2. Start with Phase 1: Backend aggregation
3. Build incrementally, testing each phase
4. Iterate on LLM prompt quality
5. Polish UI/UX in final phase

---

## Notes

- All charts should have clear titles and interpretations
- Each section should have LLM-generated insights
- Data tables should be sortable
- Consider adding export-to-PDF functionality
- Ensure consistent color schemes across all visualizations
- Add tooltips for better UX
