# Pro Investor Dashboard 
246x1120 蒲牟田倫朗
アプリurl: https://blank-app-hnzrqobbthi.streamlit.app/#eba4a695

## プロジェクト概要 (Overview)
Pro Investor Dashboard は、個人投資家向けの高度な市場分析プラットフォームです。

米国株・日本株だけでなく、債券金利、為替、暗号資産、新興国ETFなど 350種類以上の金融資産 をデータベース化しました。「価格データの可視化」「相関分析」「財務分析」に加え、APIとRSSフィードを組み合わせたハイブリッドなニュース収集システムを搭載することで、情報の網羅性と取得の安定性を両立しています。

## 主な機能 (Key Features)

### 1. マルチアセット・データベース (350+ Tickers)
- 広範なカバレッジ: 米国ハイテク株、日本株、主要ETFに加え、欧州株、インド/中国株、為替、債券利回り、暗号資産を網羅。
- ハードコーディング実装: ユーザーがコードを覚えていなくても、カテゴリから選択するだけで即座に分析可能。

### 2. 高度なチャート分析
- テクニカル指標: 移動平均線 (SMA20/50)、MACD、RSI を自動計算し、インタラクティブなチャートに描画。
- 正規化比較 (Normalized Chart): 単位の異なる銘柄（例：ビットコインと米国10年債利回り）を、開始点を0%として変動率で比較可能。

### 3. ハイブリッド・ニュースエンジン (Hybrid News Engine)
ニュース取得における「検索漏れ」を防ぐため、2つの技術を併用しています。
1. NewsAPI (Keyword Search): APIキー認証を使用。銘柄名に関連する広範なビジネスニュースを検索。
2. Yahoo Finance RSS (Direct Feed): feedparserを使用。銘柄コード（Ticker）に紐づくRSSを直接解析し、APIが苦手とする記号付き銘柄（^TNXなど）の情報を確実に取得。

### 4. データサイエンス機能
- 相関マトリクス: 選択した複数銘柄間の相関係数をヒートマップで可視化し、分散投資の効果を測定。
- ファンダメンタルズ可視化: 企業の財務諸表APIから「売上高」と「純利益」を取得しグラフ化。

---

## 技術スタックと工夫点 (Technical Highlights)

### システム構成
| Category | Technology | Description |
| --- | --- | --- |
| Frontend | Streamlit | インタラクティブなUI構築 |
| Market Data | yfinance | Yahoo Finance API経由での株価・財務データ取得 |
| News Source 1 | NewsAPI | APIキー認証によるキーワード検索型ニュース取得 |
| News Source 2 | feedparser | RSSフィードのスクレイピングによるダイレクト取得 |
| Database | Supabase | ウォッチリストの永続化 (PostgreSQL) |
| Visualization | Plotly | 動的なデータ可視化 |

### 課題解決のプロセス
1. ニュース取得の安定化
当初 NewsAPI のみを使用していたが、無料枠の制限や検索精度の問題で、ニッチな銘柄のニュースが表示されないことがあった。そこで RSSフィードの直読み（スクレイピング） をバックアップとして実装する「ハイブリッド方式」を採用。これにより、APIが記事を拾えない場合でも、Yahoo Financeのフィードから確実に情報を補完する仕組みを構築した。

2. パフォーマンス最適化
@st.cache_data を活用し、APIコールをキャッシュ化。データ取得時間を短縮しつつ、API制限（Rate Limit）にも配慮した。万が一キャッシュデータが破損した場合に備え、UI上に「キャッシュクリアボタン」を実装し、ユーザビリティを向上させた。

---

## インストールと実行方法 (Installation)

1. リポジトリのクローン
   git clone <your-repo-url>
   cd <repo-name>

2. 依存ライブラリのインストール
   pip install -r requirements.txt

3. 環境変数の設定
   .streamlit/secrets.toml ファイルを作成し、以下のAPIキーを設定してください。
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_key"
   NEWS_API_KEY = "your_newsapi_key"

4. アプリケーションの起動
   streamlit run app.py

---

## スクリーンショット

### 1. メインダッシュボード (チャート分析)
![Chart Analysis](ここにチャート画面のスクショを貼る.png)
テクニカル指標（SMA, MACD）と株価推移を同時に表示

### 2. 相関分析とニュース
![Correlation and News](ここに相関とニュース画面のスクショを貼る.png)
複数銘柄の相関ヒートマップと、ハイブリッドエンジンによるニュース一覧

---

## ディレクトリ構成

.
├── app.py                # メインアプリケーション (v13.1)
├── requirements.txt      # 依存ライブラリ一覧
├── .streamlit/
│   └── secrets.toml      # APIキー設定ファイル (Git対象外)
└── README.md             # プロジェクトドキュメント

---

Author: [あなたの名前]
