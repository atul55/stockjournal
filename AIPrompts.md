## Chatgpt
Trading Journal Applicaton - 
Create a detailed prompt for the below project. Suggest improvements or additions to the requirements based on the objective we are trying to meet. 
Act as a Software Architect. 
Create a detailed actionable plan to create a new web application with the below requirements. 

Objective - 
Build a Web Application which will help in tracking the trading performance in 
Indian Stock Markets NSE and BSE, 
Indian Commodity MCX 
Bitcoin Futures 

Requirements - 
1) Create a Trading Journal Web Application
2) Pull data from below sources - 
    a. Indian Stock Markets - NSE and BSE, Stocks, Futures, Options and Forex - Pull from Fyers
    b. Indian Commodity MCX - Futures and Options - Pull from Fyers
    c. Bitcoin Futures and Options - Pull from Delta Exchange
3) Dashboards for the earnings from each strategy 
4) Need a sub system which could analyze the trades for each strategy and suggests steps to optimize the strategy
5) Currently the data is captured manually in Excel in the attached format and used to analyze the strategy
6) Application should have a capability to generate the reports for Tax Filing in India for all the earnings and losses. 


## Gemini
# MASTER PROJECT PROMPT: MULTI-MARKET TRADING JOURNAL AND STRATEGY INTELLIGENCE PLATFORM

## 1. Role and responsibilities

Act as a Principal Software Architect, Senior Full-Stack Engineer, Quantitative Trading Systems Architect, Data Engineer and Financial Analytics Specialist.

You are responsible for designing a production-quality web application that provides a unified platform for:

1. Recording and maintaining a comprehensive trading journal.
2. Automatically retrieving trading data from supported brokers.
3. Measuring and analysing trading performance.
4. Evaluating individual trading strategies and identifying opportunities for improvement.
5. Managing trading risks and capital allocation.
6. Generating financial statements and tax-reporting data for India.

Do not treat this project as a basic CRUD application or an Excel replacement. Design it as a trading performance intelligence platform.

Your design must be modular, scalable, secure, maintainable, testable and suitable for future enhancements.

## 2. Business objective

Develop a web-based application to monitor and analyse trading activities across multiple financial markets through a common interface and centralised database.

### Supported markets and instruments

**A. Indian equity markets**

Exchanges:
- NSE
- BSE

Instruments:
- Equity stocks
- Equity futures
- Index futures
- Stock options
- Index options

Broker integration: FYERS API.

**B. Indian commodity markets**

Exchange:
- MCX

Instruments:
- Commodity futures
- Commodity options

Broker integration: FYERS API.

**C. Cryptocurrency markets**

Exchange:
- Delta Exchange India

Instruments:
- Bitcoin futures
- Bitcoin perpetual futures, where supported
- Bitcoin call options
- Bitcoin put options

Broker integration: Delta Exchange API.

**D. Currency and forex markets**

Intended scope:
- Permitted exchange-traded currency futures and options.
- Historical currency derivative trade imports.
- Manual trade recording where appropriate.

Broker integration: FYERS, subject to actual segment availability and applicable regulatory permissions.

Do not assume that FYERS currently permits new currency derivative positions. Implement this segment as a configurable capability that can be enabled only when the broker confirms support.

Do not introduce unsupported offshore forex or CFD trading functionality.

## 3. Existing Excel application and migration

An existing Excel workbook named `StockJournal.xlsx` is used for recording trades and analysing strategy performance.

It contains:
- Self
- Algo
- Reyansh
- Crypto
- Self_Final
- Reyansh_Final
- Crypto_Final
- Self_Strategies

The existing journal follows a parent-trade and multiple-leg structure.

Each parent trade includes:
- Entry date
- Exit date
- Number of trading days
- Strategy name
- Strategy source / suggested by
- Comments and learnings
- Margin used
- Consolidated gross profit/loss
- Charges
- Net profit/loss
- Profit/loss percentage

Each instrument leg includes:
- Instrument/contract name
- Buy or Sell
- Entry price
- Underlying spot price at entry
- Entry date and time
- Exit price
- Underlying spot price at exit
- Exit date and time
- Quantity/lot size
- Gross profit/loss
- Trading fees and charges
- Net profit/loss

The cryptocurrency journal additionally records entry and exit trading fees separately.

### Migration requirements

Create an Excel import subsystem that:

1. Allows uploading an existing Excel workbook.
2. Identifies individual trade blocks and instrument legs.
3. Maps existing columns to the new data model.
4. Identifies duplicate trades across worksheets.
5. Identifies missing dates, incomplete prices, invalid quantities and inconsistent values.
6. Separates detailed source records from summary worksheets.
7. Displays an import preview before committing data.
8. Provides a manual correction and field-mapping interface.
9. Supports re-importing without creating duplicate trades.
10. Generates a migration reconciliation report.

Do not import summary worksheets as additional trades when they represent already imported detail records.

Preserve the original Excel data as an audit source.

## 4. Functional requirements

### Module 1: User management and account configuration

Provide:
- Secure authentication.
- User profile and preferences.
- Multiple broker accounts.
- Multiple trading accounts or subaccounts where supported.
- Broker connection configuration.
- Account-wise trading capital.
- Base reporting currency, initially INR.
- Financial year/tax year configuration.
- User-defined trading strategies.
- Strategy categories and tags.

The architecture should initially support a private individual trading workspace while allowing future multi-user expansion.

### Module 2: Broker integration and automated data collection

Implement independent broker connector modules.

#### FYERS integration

Integrate the official FYERS API.

Implement:
- Broker authentication and token management.
- Trade history retrieval.
- Order history retrieval.
- Position retrieval.
- Realised P&L retrieval.
- Charges report retrieval.
- Tax P&L retrieval.
- Account ledger retrieval.
- Historical market data retrieval.
- Instrument/symbol master retrieval.
- Historical and expired F&O contract information where available.

Support:
- NSE equity
- NSE derivatives
- BSE equity
- BSE derivatives
- MCX commodity derivatives

Handle currency derivatives according to the broker's actual permissions and availability.

#### Delta Exchange integration

Use the India production API and official documentation.

Implement:
- API key authentication and request signing.
- Product and instrument master retrieval.
- Executed fills retrieval.
- Order history retrieval.
- Position retrieval.
- Wallet transactions retrieval.
- Trading fees and commission retrieval.
- Funding payments where applicable.
- Realised P&L retrieval.
- Contract settlement information.
- Historical market data where available.

Support BTC futures, perpetual futures and options.

Ensure that the application captures the actual quoting asset and settlement asset for every contract.

#### Common integration requirements

All connectors must implement a common interface.

Provide:
- Automatic scheduled synchronisation.
- Manual synchronisation.
- Initial historical data import.
- Incremental data synchronisation.
- Retry handling.
- Rate-limit handling.
- Pagination.
- Sync checkpoints.
- Error logging.
- Duplicate prevention.
- Historical backfill.
- Data reconciliation.

Store the original broker response in a raw-data archive before normalising it.

Use broker execution/fill records as the primary evidence of executed trades. Broker P&L, tax reports and ledgers must be used for reconciliation.

Do not assume broker APIs provide unlimited historical trade retention.

Create a manual CSV/Excel import fallback when API access or historical availability is insufficient.

**Important:** This application is a read-only journal and analytics system. Do not implement live order placement, cancellation or automated trading in the initial release.

### Module 3: Centralised trading journal

Create a unified journal for all exchanges and instruments.

Use a hierarchical structure:

Trading Account → Strategy Trade → Trade Legs → Executions/Fills.

A parent trade represents one strategy instance or trading idea.

A trade can contain any number of instrument legs.

A leg can contain multiple partial executions.

A parent trade must support:
- Draft
- Planned
- Open
- Partially closed
- Closed
- Expired
- Adjusted
- Rolled over
- Assigned/exercised
- Reconciliation required

Capture the following details:

**Trade-level information**
- Unique trade ID
- Broker and trading account
- Exchange
- Market segment
- Strategy
- Strategy version
- Strategy source/suggested by
- Entry date
- Exit date
- Holding period
- Margin used
- Capital at risk
- Trade status
- Comments
- Trading rationale
- Market conditions
- Entry reason
- Exit reason
- Lessons learned
- Attachments/screenshots

**Leg-level information**
- Instrument symbol
- Underlying
- Instrument type
- Expiry
- Strike
- Call/Put
- Buy/Sell
- Entry and exit quantities
- Number of lots
- Contract lot size/multiplier
- Entry price
- Exit price
- Entry and exit timestamps
- Underlying spot/index price
- Brokerage
- Exchange fees
- Taxes
- Other charges
- Gross P&L
- Net P&L

Keep quantity, lot count and contract lot size as separate fields.

Provide manual trade entry, trade editing, leg adjustment and broker-execution assignment interfaces.

### Module 4: Trading strategy management

Allow users to create and maintain reusable strategy definitions.

Examples:
- Short Straddle
- Short Strangle
- Iron Condor
- Iron Butterfly
- Calendar Spread
- Ratio Spread
- Bull Put Spread
- Bear Call Spread
- Intraday Scalping
- Trend Following
- Breakout Trading
- Custom user-defined strategies

Each strategy should support:

- Strategy name
- Market and instrument compatibility
- Strategy description
- Entry rules
- Exit rules
- Stop-loss rules
- Target rules
- Position sizing
- Maximum risk
- Required capital/margin
- Expiry selection
- Strike-selection methodology
- Indicators and market conditions
- Strategy parameters
- Strategy version history

Separate the strategy itself from its signal source or strategy provider.

For example, Short Strangle is a strategy, while a YouTube channel or Telegram group is its source.

Historical trades must retain the strategy version that was applicable when they were executed.

### Module 5: P&L and trading accounting engine

Develop a central accounting engine for calculating the financial performance of trades.

It must correctly support:
- Long and short equity positions.
- Futures.
- Options.
- Multiple option legs.
- Partial entry and exit.
- Position averaging.
- Scale-in and scale-out.
- Expiry and settlement.
- Exercise and assignment where applicable.
- Contract multipliers.
- Commodity-specific contract specifications.
- Cryptocurrency derivative settlement.
- Funding payments for perpetual futures.
- Liquidation and liquidation fees.

Calculate and store separately:

1. Gross realised P&L.
2. Brokerage.
3. Exchange transaction charges.
4. STT, where applicable.
5. GST, where applicable.
6. Stamp duty, where applicable.
7. SEBI charges, where applicable.
8. CTT, where applicable.
9. Trading fees.
10. Funding income or expense.
11. Other broker charges.
12. Net realised P&L.
13. Unrealised P&L.
14. Total account P&L.
15. Margin/capital utilised.
16. ROI percentage.

Use broker-provided charges wherever available rather than relying exclusively on estimated fee calculations.

Maintain a configurable and effective-date-based fee schedule as a fallback.

The calculations must be instrument-specific and currency-aware.

For cryptocurrency contracts, store original P&L and fees in their settlement currency and maintain the INR conversion information separately.

Maintain a distinction between trade-level ROI based on margin and return based on actual account equity or capital at risk.

Provide a detailed breakdown so that every consolidated P&L figure can be traced to its underlying executions and charges.

### Module 6: Performance dashboards

Build a professional dashboard with filters for:

- Date range
- Financial year
- Broker
- Trading account
- Exchange
- Market
- Segment
- Instrument type
- Strategy
- Strategy version
- Strategy source
- Underlying
- Long/short
- Intraday/positional
- Expiry
- Trade status

#### Overall performance dashboard

Display:
- Total net profit/loss.
- Gross profit/loss.
- Total trading charges.
- Realised P&L.
- Unrealised P&L.
- Number of trades.
- Winning trades.
- Losing trades.
- Win rate.
- Average profit per trade.
- Average loss per trade.
- Profit factor.
- Expectancy.
- Maximum drawdown.
- Return on capital.
- Maximum consecutive wins.
- Maximum consecutive losses.
- Average holding period.
- Capital deployed.
- Margin utilisation.

Include:
- Equity curve.
- Monthly performance chart.
- Daily P&L chart.
- Monthly returns heatmap.
- Strategy-wise distribution.
- Market-wise comparison.
- Drawdown chart.
- Cumulative profits and losses.

#### Strategy-wise dashboard

For every strategy show:
- Total P&L.
- Gross and net P&L.
- Number of trades.
- Win rate.
- Average winning trade.
- Average losing trade.
- Average ROI.
- Expectancy.
- Profit factor.
- Maximum drawdown.
- Best and worst trade.
- Average holding period.
- Trading charges.
- Performance by weekday.
- Performance by time of day.
- Performance by underlying.
- Performance by market condition.

Provide a comparison dashboard to compare two or more strategies over the same period and capital assumptions.

#### Strategy source dashboard

Analyse performance based on the person, advisor, YouTube channel or other source from which the strategy was obtained.

Show which sources have generated the best and worst risk-adjusted performance.

### Module 7: Strategy intelligence and optimisation engine

Develop an analytics subsystem that evaluates historical trading performance and generates suggestions for improving individual strategies.

This is one of the most important parts of the application.

The objective is to identify measurable opportunities to improve performance rather than generate generic trading advice.

#### A. Quantitative analysis

Calculate:
- Win rate.
- Profit factor.
- Expectancy.
- Average risk/reward.
- Average winning trade.
- Average losing trade.
- Maximum drawdown.
- Maximum adverse excursion where data supports it.
- Maximum favourable excursion where data supports it.
- Sharpe ratio where statistically appropriate.
- Sortino ratio where statistically appropriate.
- Recovery factor.
- Consecutive wins/losses.
- Holding-period distribution.
- Transaction cost impact.
- Slippage where benchmark data is available.

#### B. Performance segmentation

Analyse strategy performance by:
- Time of day.
- Day of week.
- Expiry day versus non-expiry day.
- Days to expiry.
- Market volatility.
- India VIX/volatility regime where relevant.
- Trending versus sideways market.
- Underlying index/stock.
- Trading session.
- Position size.
- Margin utilisation.
- Entry and exit conditions.

#### C. Optimisation recommendations

Generate evidence-based suggestions such as:
- Preferred entry time.
- Avoided entry time.
- Preferred expiry selection.
- Optimal holding period.
- Position sizing adjustments.
- Stop-loss adjustments.
- Profit-taking adjustments.
- Underlying selection.
- Market conditions in which the strategy historically performed poorly.
- Reduction in trading charges.
- Poor-performing strategy variants.
- Potential changes in entry and exit rules.

Each recommendation must include:
- The finding.
- Supporting data.
- Relevant sample size.
- Historical performance comparison.
- Estimated impact.
- Confidence/limitations.
- Suggested experiment.
- Backtesting or validation status.

Do not generate recommendations solely on a small number of trades.

Avoid overfitting historical data.

Implement train/test separation or walk-forward validation for strategy parameter experiments where sufficient data exists.

Separate observed historical relationships from proven causal effects.

An AI/LLM component may explain findings in plain English, but all financial calculations must come from deterministic and testable analytics code.

Never claim that a strategy modification guarantees future profits.

### Module 8: Market data and trading context

Capture relevant market information at the time of trade entry and exit.

Where available, retrieve:
- Underlying spot price.
- OHLC candles.
- India VIX.
- Implied volatility.
- Option Greeks.
- Open interest.
- Change in open interest.
- Volume.
- Bid/ask prices.
- Futures prices.
- Expiry details.
- Funding rates for perpetual crypto contracts.

Do not require expensive real-time data for all metrics in the initial version.

Prioritise reliable historical data for explaining strategy performance.

Store data source, timestamp, timezone and quality information.

### Module 9: Indian tax reporting subsystem

Create an Indian tax-reporting module capable of producing accountant-ready financial reports for the relevant tax year.

The design must support different tax classifications and reporting rules for:
- Delivery-based equity trades.
- Intraday equity transactions.
- Equity futures and options.
- Index futures and options.
- MCX commodity futures and options.
- Permitted currency derivatives.
- Bitcoin futures and options.

Create a versioned tax-rule engine.

Tax classifications, turnover calculations, expense treatment, carry-forward information and report templates must be configurable by tax year, taxpayer type and instrument category.

Do not assume that all markets have identical tax treatment.

Do not hardcode one turnover calculation for every instrument.

Cryptocurrency derivative treatment must remain separately configurable and should be reviewed by an Indian tax professional.

Provide reports including:

**A. Trading profit and loss**
- Exchange-wise P&L.
- Instrument-wise P&L.
- Segment-wise P&L.
- Realised profit/loss.
- Trading expenses.
- Net business/investment results under the applicable classification.

**B. Turnover and audit preparation**
- Applicable intraday turnover.
- Applicable futures/options turnover.
- Exchange-wise turnover.
- Supporting trade-level calculations.
- Configurable audit-reporting calculations.
- Data for tax professional review.

**C. Supporting financial statements**
- Trading account.
- Profit and loss statement.
- Ledger statement.
- Charges statement.
- Trade execution statement.
- Open positions report.
- Realised P&L report.
- Funding and other crypto transaction reports.
- Broker reconciliation statement.

**D. Tax year management**
- Financial/tax year selection.
- Prior-year closing balances.
- Loss and carry-forward tracking.
- Applicable tax-rule version.
- Report version and generation date.

Allow reports to be exported to Excel, CSV and PDF.

The reporting engine must support updates to Indian income-tax laws, rules and notified return forms.

Do not submit income-tax returns automatically in the first release. The application must generate supporting information for the user and their Chartered Accountant.

Clearly label tax estimates and reports as subject to professional review.

### Module 10: Reporting and exports

Provide:
- Trade-level reports.
- Strategy reports.
- Broker reports.
- Instrument reports.
- Monthly reports.
- Daily reports.
- Tax reports.
- Risk reports.
- Excel export.
- CSV export.
- PDF export.

Every report should allow configurable filters and date ranges.

### Module 11: Notifications and alerts

Provide optional notifications for:
- Data synchronisation failures.
- Unmatched broker executions.
- Incomplete trades.
- Missing entry or exit information.
- Unusually high trading costs.
- Strategy drawdown thresholds.
- Daily or weekly performance summaries.
- Strategy performance deterioration.

Support email and in-app notifications initially.

### Module 12: Audit trail and data integrity

Maintain an audit log of:
- Trade creation.
- Trade modifications.
- Strategy changes.
- Manual P&L overrides.
- Broker imports.
- Data synchronisation.
- Tax report generation.
- User corrections.

Never silently overwrite the original broker execution data.

Maintain a clear distinction between broker-sourced, manually entered, calculated and user-adjusted values.

## 5. Technical architecture

Recommend and validate a technology stack.

Use the following as the preferred starting point unless you identify a strong technical reason to change it.

### Frontend
- React / Next.js.
- TypeScript.
- Responsive desktop-first UI.
- Tailwind CSS.
- Professional dashboard components.
- Interactive charts.

### Backend
- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- Alembic database migrations.

### Database
- PostgreSQL.
- Decimal-safe financial calculations.
- Transaction-safe writes.
- JSONB raw broker payload storage where appropriate.

### Background processing
- Redis.
- Celery or an appropriate Python job-processing framework.
- Scheduled synchronisation tasks.
- Retry and checkpoint management.

### Storage
- Local/S3-compatible object storage for statements, Excel imports and screenshots.

### Deployment
- Docker.
- Docker Compose for development.
- Production container deployment.
- Environment-based configuration.

### Architecture style

Prefer a modular monolith initially instead of introducing unnecessary microservices.

Maintain distinct logical modules for:
1. Authentication.
2. Broker integrations.
3. Data ingestion.
4. Instrument master.
5. Trading journal.
6. Accounting