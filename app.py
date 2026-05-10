from flask import Flask, request, jsonify, render_template_string
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.summarizer import SummaryWriter

app = Flask(__name__)
summarizer = SummaryWriter(target_words=60)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="icon" type="image/png" href="{{ url_for('static', filename='logo.png') }}">
  <title>Summary Writer</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Segoe UI', Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(126, 217, 87, 0.16), transparent 34%),
        radial-gradient(circle at bottom right, rgba(4, 120, 87, 0.12), transparent 30%),
        linear-gradient(135deg, #f5fff8 0%, #ecfdf5 45%, #f9fffb 100%);
      color: #12372a;
      min-height: 100vh;
    }

    header {
      width: 100%; height: 50%;
      background: linear-gradient(135deg, #023c2e 0%, #056447 55%, #84d65a 100%);
      color: white; padding: 24px 38px;
      box-shadow: 0 14px 36px rgba(4, 120, 87, 0.28);
      border-bottom-left-radius: 30px; border-bottom-right-radius: 30px;
    }

    .header-content {
      width: 100%; display: flex; align-items: center;
      justify-content: flex-start; gap: 24px;
    }

    .title-area h1 {
     font-family: Georgia, 'Times New Roman', serif;
     font-style: italic; font-size: 2.25rem; font-weight: 900;
     letter-spacing: -1px; line-height: 1.1; color: #ffffff;
    }

    .logo-writer {
     color: #7ed957; font-style: italic;
    }

    .logo {
      width: 50px; height: auto; object-fit: contain;
      background: transparent; padding: 0; border: none; 
      border-radius: 0; box-shadow: none; display: block; flex-shrink: 0;
    }
    .container { max-width: 960px; margin: 40px auto; padding: 0 20px; }
    .card {
      background: white;
      border-radius: 12px;
      padding: 32px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
      margin-bottom: 24px;
    }
    .card h2 { font-size: 1.1rem; color: #000000; margin-bottom: 16px;
               border-left: 4px solid #84D65A; padding-left: 10px; font-weight: 700}
    textarea {
      width: 100%; min-height: 200px; padding: 14px;
      border: 2px solid #20C900; border-radius: 20px;
      font-size: 0.95rem; line-height: 1.6; resize: vertical;
      font-family: inherit; transition: border-color 0.2s;
    }
    textarea:focus { outline: none; border-color: #2AFA02; }
    .controls { display: flex; gap: 12px; margin-top: 16px; align-items: center; }
    button {
      background: #20C900; color: white; border: none; padding: 12px 28px;
      border-radius: 20px; font-size: 1rem; cursor: pointer; font-weight: 600;
      transition: background 0.2s;
    }
    button:hover { background: #25E300; }
    button.secondary {
      background: #e2e8f0; color: #4a5568; font-weight: 500;
    }
    button.secondary:hover { background: #cbd5e0; }
    .word-count { font-size: 0.85rem; color: #718096; }
    .summary-box {
      background: #f5fff8; border: 2px solid #2AFA02;
      border-radius: 20px; padding: 20px; font-size: 1.05rem;
      line-height: 1.8; color: #2c5282; text-align: justify;
    }
    .badge {
      display: inline-block; background: #3FA135; color: white; height: 100%;
      font-size: 0.75rem; padding: 3px 10px; border-radius: 20px;
      font-weight: 600; margin-left: 8px; font-style: normal;
    }
    .score-table { width: 100%; border-collapse: collapse; font-size: 0.88rem;}
    .score-table th {
      background: #E2F0E5; text-align: left; padding: 8px 12px;
      border-bottom: 2px solid #E2F0E7;;
    }
    .score-table td { padding: 8px 12px; border-bottom: 1px solid #D1D1D1;}
    .score-table tr:hover td { background: #F2FFF4;}
    .bar-wrap { background: #E2F0E5; border-radius: 4px; height: 8px; min-width: 60px; }
    .bar      { background: #4AA85D; border-radius: 4px; height: 8px; }
    .highlight { background: #BFFEC6; font-weight: 600; }
    .tag { display:inline-block; background:#04D448; color:#276749;
           border-radius:4px; padding:2px 7px; font-size:0.75rem; margin-left:4px;}
    .error { background: #fff5f5; border: 2px solid #feb2b2;
             color: #c53030; border-radius: 20px; padding: 16px; }
    .loader { display:none; margin-left:12px; font-size:0.9rem; color:#718096; }
    footer { text-align:center; color:#a0aec0; font-size:0.82rem;
             margin: 40px 0 20px; }
  </style>
</head>
<body>
<header>
  <div class="header-content">
    <img src="/static/logo.png" alt="Summary Writer Logo" class="logo">
    <div class="title-area">
      <h1>Summary <span class="logo-writer">Writer</span></h1>
    </div>
  </div>
</header>

<div class="container">

  <!-- Input Card -->
  <div class="card">
    <h2>Input Article</h2>
    <textarea id="article" placeholder="Paste a news article here (minimum 100 words)"></textarea>
    <div class="controls">
      <button onclick="summarise()">Summarise (60 words)</button>
      <button class="secondary" onclick="clearAll()">🗑 Clear</button>
      <span class="loader" id="loader">Analysing…</span>
      <span class="word-count" id="input-wc"></span>
    </div>
  </div>

  <!-- Output Card -->
  <div id="output-section" style="display:none">
    <div class="card">
      <h2>Summary Result <span id="wc-badge" class="badge"></span></h2>
      <div class="summary-box" id="summary-text"></div>
    </div>

    <!-- Algorithm Detail -->
    <div class="card">
      <h2>Algorithm Transparency & Sentence Scores</h2>
      <table class="score-table">
        <thead>
          <tr>
            <th>No</th><th>Sentence Preview</th>
            <th>TF-IDF</th><th>Cosine Sim</th>
            <th>Final Score</th><th>Score Bar</th>
          </tr>
        </thead>
        <tbody id="score-tbody"></tbody>
      </table>
    </div>
  </div>

  <div id="error-box" class="error" style="display:none"></div>
</div>

<footer></footer>

<script>
  const articleEl = document.getElementById('article');
  articleEl.addEventListener('input', () => {
    const n = articleEl.value.trim().split(/\s+/).filter(Boolean).length;
    document.getElementById('input-wc').textContent = n + ' words';
  });
  articleEl.dispatchEvent(new Event('input'));

  async function summarise() {
    const text = articleEl.value.trim();
    if (!text) { alert('Please paste an article first.'); return; }
    document.getElementById('loader').style.display = 'inline';
    document.getElementById('output-section').style.display = 'none';
    document.getElementById('error-box').style.display = 'none';

    try {
      const resp = await fetch('/summarise', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({article: text})
      });
      const data = await resp.json();
      if (data.error) throw new Error(data.error);

      document.getElementById('summary-text').textContent = data.summary;
      document.getElementById('wc-badge').textContent = data.word_count + ' words';

      const tbody = document.getElementById('score-tbody');
      tbody.innerHTML = '';
      const maxScore = data.scores[0]?.final_score || 1;
      data.scores.forEach(s => {
        const pct = Math.round((s.final_score / maxScore) * 100);
        const sel = data.selected.includes(s.index);
        tbody.innerHTML += `<tr class="${sel ? 'highlight' : ''}">
          <td>${s.rank}</td>
          <td>${s.sentence}${sel ? '<span class="tag">selected</span>' : ''}</td>
          <td>${s.tfidf_score}</td>
          <td>${s.sim_score}</td>
          <td><strong>${s.final_score}</strong></td>
          <td><div class="bar-wrap"><div class="bar" style="width:${pct}%"></div></div></td>
        </tr>`;
      });
      document.getElementById('output-section').style.display = 'block';
    } catch(e) {
      document.getElementById('error-box').textContent = 'Error: ' + e.message;
      document.getElementById('error-box').style.display = 'block';
    }
    document.getElementById('loader').style.display = 'none';
  }

  function clearAll() {
    articleEl.value = '';
    document.getElementById('output-section').style.display = 'none';
    document.getElementById('error-box').style.display = 'none';
    articleEl.dispatchEvent(new Event('input'));
  }
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/summarise', methods=['POST'])
def api_summarise():
    data = request.get_json(force=True)
    article = data.get('article', '').strip()
    if not article:
        return jsonify({'error': 'No article text provided.'}), 400
    try:
        summary, debug = summarizer.summarise(article)
        return jsonify({
            'summary': summary,
            'word_count': debug.get('word_count', len(summary.split())),
            'scores': debug.get('sentence_scores', []),
            'selected': debug.get('selected_indices', []),
        })
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


if __name__ == '__main__':
    print("=" * 55)
    print(" SummaryWriter Web App")
    print(" Open: http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
