-- Table: public.user_roles

-- DROP TABLE IF EXISTS public.user_roles;

CREATE TABLE IF NOT EXISTS public.user_roles
(
    role_id integer NOT NULL DEFAULT nextval('user_roles_role_id_seq'::regclass),
    role_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT user_roles_pkey PRIMARY KEY (role_id),
    CONSTRAINT user_roles_role_name_key UNIQUE (role_name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.user_roles
    OWNER to db_user;

INSERT INTO user_roles (role_name) VALUES ('Trader'), ('Manager');

-- Table: public.auth

-- DROP TABLE IF EXISTS public.auth;

CREATE TABLE IF NOT EXISTS public.auth
(
    id integer NOT NULL DEFAULT nextval('auth_id_seq'::regclass),
    display_name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    password_hash character(60) COLLATE pg_catalog."default" NOT NULL,
    email character varying(255) COLLATE pg_catalog."default" NOT NULL,
    role_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    can_trade boolean DEFAULT false,
    account_disabled boolean DEFAULT false,
    CONSTRAINT auth_pkey PRIMARY KEY (id),
    CONSTRAINT auth_display_name_key UNIQUE (display_name),
    CONSTRAINT auth_email_key UNIQUE (email),
    CONSTRAINT fk_role_id FOREIGN KEY (role_id)
        REFERENCES public.user_roles (role_id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.auth
    OWNER to db_user;

-- Register first user as Trader

-- Table: public.watchlist

-- DROP TABLE IF EXISTS public.watchlist;

CREATE TABLE IF NOT EXISTS public.watchlist
(
    id integer NOT NULL DEFAULT nextval('watchlist_id_seq'::regclass),
    user_id integer NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    display_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    type character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT watchlist_pkey PRIMARY KEY (id),
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.watchlist
    OWNER to db_user;

-- Table: public.trade_state

-- DROP TABLE IF EXISTS public.trade_state;

CREATE TABLE IF NOT EXISTS public.trade_state
(
    id integer NOT NULL DEFAULT nextval('trade_state_id_seq'::regclass),
    state character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT trade_state_pkey PRIMARY KEY (id),
    CONSTRAINT trade_state_state_key UNIQUE (state)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trade_state
    OWNER to db_user;       

INSERT INTO trade_state (state) VALUES ('open'), ('reduced'), ('closed');

-- Table: public.cash_balances

-- DROP TABLE IF EXISTS public.cash_balances;

CREATE TABLE IF NOT EXISTS public.cash_balances
(
    id integer NOT NULL DEFAULT nextval('cash_balances_id_seq'::regclass),
    trader_id integer,
    balance numeric(15,5) NOT NULL,
    last_update timestamp with time zone DEFAULT now(),
    description text COLLATE pg_catalog."default",
    margin_used numeric(15,5) DEFAULT 0,
    margin_available numeric(15,5) DEFAULT 0,
    nav numeric(15,5) DEFAULT 0,
    initial_balance numeric(15,5) DEFAULT 0,
    CONSTRAINT cash_balances_pkey PRIMARY KEY (id),
    CONSTRAINT cash_balances_trader_id_fkey FOREIGN KEY (trader_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.cash_balances
    OWNER to db_user;

INSERT INTO cash_balances (balance, description)
VALUES (10000, 'Unallocated Capital');

-- Table: public.trades

-- DROP TABLE IF EXISTS public.trades;

CREATE TABLE IF NOT EXISTS public.trades
(
    id integer NOT NULL DEFAULT nextval('trades_id_seq'::regclass),
    user_id integer,
    open_time timestamp with time zone NOT NULL,
    current_units numeric(10,3) NOT NULL,
    financing numeric(12,5) NOT NULL,
    transaction_id character varying(10) COLLATE pg_catalog."default" NOT NULL,
    initial_units numeric(10,3) NOT NULL,
    instrument character varying(50) COLLATE pg_catalog."default" NOT NULL,
    price numeric(12,5) NOT NULL,
    realized_pl numeric(12,5) NOT NULL DEFAULT 0.0000,
    unrealized_pl numeric(12,5) NOT NULL DEFAULT 0.0000,
    state_id integer NOT NULL,
    update_time timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    margin_used numeric(12,5) NOT NULL DEFAULT 0.0000,
    close_time timestamp with time zone,
    CONSTRAINT trades_pkey PRIMARY KEY (id),
    CONSTRAINT trades_transaction_id_key UNIQUE (transaction_id),
    CONSTRAINT fk_state_id FOREIGN KEY (state_id)
        REFERENCES public.trade_state (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trades
    OWNER to db_user;

-- Table: public.trade_audit

-- DROP TABLE IF EXISTS public.trade_audit;

CREATE TABLE IF NOT EXISTS public.trade_audit
(
    trade_id integer NOT NULL,
    user_id integer NOT NULL,
    net_realized_pl numeric(15,5) NOT NULL,
    close_time timestamp with time zone NOT NULL,
    CONSTRAINT trade_audit_pkey PRIMARY KEY (trade_id),
    CONSTRAINT fk_trade_id FOREIGN KEY (trade_id)
        REFERENCES public.trades (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.trade_audit
    OWNER to db_user;

-- Table: public.oanda_transaction_log

-- DROP TABLE IF EXISTS public.oanda_transaction_log;

CREATE TABLE IF NOT EXISTS public.oanda_transaction_log
(
    id integer NOT NULL DEFAULT nextval('oanda_transaction_log_id_seq'::regclass),
    last_transaction_id integer NOT NULL,
    recorded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT oanda_transaction_log_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.oanda_transaction_log
    OWNER to db_user;

-- Table: public.strategy_type

-- DROP TABLE IF EXISTS public.strategy_type;

CREATE TABLE IF NOT EXISTS public.strategy_type
(
    id integer NOT NULL DEFAULT nextval('strategy_type_id_seq'::regclass),
    type character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT strategy_type_pkey PRIMARY KEY (id),
    CONSTRAINT strategy_type_type_key UNIQUE (type)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.strategy_type
    OWNER to db_user;

INSERT INTO strategy_type (type) VALUES
	('Arbitrage'), ('Mean reversion'), ('Trend following'), ('High-frequency trading'), 
    ('Market making'), ('Pairs trading'), ('Momentum'), ('Algorithmic trading'), 
    ('Machine learning'), ('Forex scalping'), ('Index fund rebalancing'), ('Day trading algorithms'), 
    ('Execution'), ('Market sentiment'), ('Momentum trading'), ('Weighted average price strategy'),
     ('Hedging algorithms'), ('Market timing'), ('Sentiment analysis'), ('VWAP'), ('Black swan Catchers'),
      ('Conclusion'), ('Day trading automation'), ('Direct market access');

-- Table: public.strategies

-- DROP TABLE IF EXISTS public.strategies;

CREATE TABLE IF NOT EXISTS public.strategies
(
    id integer NOT NULL DEFAULT nextval('strategies_id_seq'::regclass),
    owner_id integer NOT NULL,
    type integer NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    comments character varying(500) COLLATE pg_catalog."default" NOT NULL,
    script_path character varying(500) COLLATE pg_catalog."default" NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT strategies_pkey PRIMARY KEY (id),
    CONSTRAINT fk_owner_id FOREIGN KEY (owner_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_type FOREIGN KEY (type)
        REFERENCES public.strategy_type (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.strategies
    OWNER to db_user;

-- Table: public.active_strategies_trades

-- DROP TABLE IF EXISTS public.active_strategies_trades;

CREATE TABLE IF NOT EXISTS public.active_strategies_trades
(
    id integer NOT NULL DEFAULT nextval('active_strategies_trades_id_seq'::regclass),
    user_id integer NOT NULL,
    strategy_id integer NOT NULL,
    instrument character varying(50) COLLATE pg_catalog."default" NOT NULL,
    trade_id integer,
    is_active boolean NOT NULL,
    pid integer,
    CONSTRAINT active_strategies_trades_pkey PRIMARY KEY (id),
    CONSTRAINT fk_instrument FOREIGN KEY (instrument)
        REFERENCES public.instruments (name) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_strategy_id FOREIGN KEY (strategy_id)
        REFERENCES public.strategies (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_trade_id FOREIGN KEY (trade_id)
        REFERENCES public.trades (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT fk_user_id FOREIGN KEY (user_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.active_strategies_trades
    OWNER to db_user;
-- Index: idx_unique_active_strategies_instruments

-- DROP INDEX IF EXISTS public.idx_unique_active_strategies_instruments;

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_strategies_instruments
    ON public.active_strategies_trades USING btree
    (user_id ASC NULLS LAST, strategy_id ASC NULLS LAST, instrument COLLATE pg_catalog."default" ASC NULLS LAST)
    TABLESPACE pg_default
    WHERE trade_id IS NULL;
-- Index: idx_unique_active_strategies_instruments_with_trade

-- DROP INDEX IF EXISTS public.idx_unique_active_strategies_instruments_with_trade;

CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_active_strategies_instruments_with_trade
    ON public.active_strategies_trades USING btree
    (user_id ASC NULLS LAST, strategy_id ASC NULLS LAST, instrument COLLATE pg_catalog."default" ASC NULLS LAST, trade_id ASC NULLS LAST)
    TABLESPACE pg_default
    WHERE trade_id IS NOT NULL;


-- Table: public.orders

-- DROP TABLE IF EXISTS public.orders;

CREATE TABLE IF NOT EXISTS public.orders
(
    id integer NOT NULL DEFAULT nextval('orders_id_seq'::regclass),
    trader_id integer NOT NULL,
    order_id integer NOT NULL,
    completed boolean NOT NULL DEFAULT false,
    CONSTRAINT orders_pkey PRIMARY KEY (id),
    CONSTRAINT orders_order_id_key UNIQUE (order_id),
    CONSTRAINT fk_trader_id FOREIGN KEY (trader_id)
        REFERENCES public.auth (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.orders
    OWNER to db_user;

-- Table: public.instruments

-- DROP TABLE IF EXISTS public.instruments;

CREATE TABLE IF NOT EXISTS public.instruments
(
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    type character varying(50) COLLATE pg_catalog."default" NOT NULL,
    display_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT instruments_pkey PRIMARY KEY (name)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.instruments
    OWNER to db_user;

INSERT INTO instruments (name, type, display_name) VALUES
  ('HKD_JPY', 'CURRENCY', 'HKD/JPY'),
  ('US2000_USD', 'CFD', 'US Russ 2000'),
  ('USD_SGD', 'CURRENCY', 'USD/SGD'),
  ('EUR_SEK', 'CURRENCY', 'EUR/SEK'),
  ('GBP_PLN', 'CURRENCY', 'GBP/PLN'),
  ('SUGAR_USD', 'CFD', 'Sugar'),
  ('EUR_PLN', 'CURRENCY', 'EUR/PLN'),
  ('DE10YB_EUR', 'CFD', 'Bund'),
  ('GBP_NZD', 'CURRENCY', 'GBP/NZD'),
  ('XAU_USD', 'METAL', 'Gold'),
  ('UK100_GBP', 'CFD', 'UK 100'),
  ('JP225Y_JPY', 'CFD', 'Japan 225 (JPY)'),
  ('EUR_NOK', 'CURRENCY', 'EUR/NOK'),
  ('US30_USD', 'CFD', 'US Wall St 30'),
  ('USD_CZK', 'CURRENCY', 'USD/CZK'),
  ('EUR_GBP', 'CURRENCY', 'EUR/GBP'),
  ('CHF_HKD', 'CURRENCY', 'CHF/HKD'),
  ('XAG_USD', 'METAL', 'Silver'),
  ('EUR_CZK', 'CURRENCY', 'EUR/CZK'),
  ('NZD_JPY', 'CURRENCY', 'NZD/JPY'),
  ('EUR_HUF', 'CURRENCY', 'EUR/HUF'),
  ('WHEAT_USD', 'CFD', 'Wheat'),
  ('XAU_AUD', 'METAL', 'Gold/AUD'),
  ('XAU_CAD', 'METAL', 'Gold/CAD'),
  ('CH20_CHF', 'CFD', 'Switzerland 20'),
  ('CAD_HKD', 'CURRENCY', 'CAD/HKD'),
  ('BCH_USD', 'CFD', 'Bitcoin Cash'),
  ('XAG_CHF', 'METAL', 'Silver/CHF'),
  ('USD_CHF', 'CURRENCY', 'USD/CHF'),
  ('XAG_HKD', 'METAL', 'Silver/HKD'),
  ('AUD_HKD', 'CURRENCY', 'AUD/HKD'),
  ('ESPIX_EUR', 'CFD', 'Spain 35'),
  ('NZD_CHF', 'CURRENCY', 'NZD/CHF'),
  ('AUD_CHF', 'CURRENCY', 'AUD/CHF'),
  ('GBP_CHF', 'CURRENCY', 'GBP/CHF'),
  ('USD_THB', 'CURRENCY', 'USD/THB'),
  ('XAU_JPY', 'METAL', 'Gold/JPY'),
  ('XAU_HKD', 'METAL', 'Gold/HKD'),
  ('GBP_CAD', 'CURRENCY', 'GBP/CAD'),
  ('EUR_HKD', 'CURRENCY', 'EUR/HKD'),
  ('CHF_JPY', 'CURRENCY', 'CHF/JPY'),
  ('GBP_HKD', 'CURRENCY', 'GBP/HKD'),
  ('EUR_NZD', 'CURRENCY', 'EUR/NZD'),
  ('XAG_AUD', 'METAL', 'Silver/AUD'),
  ('WTICO_USD', 'CFD', 'West Texas Oil'),
  ('XAG_NZD', 'METAL', 'Silver/NZD'),
  ('CN50_USD', 'CFD', 'China A50'),
  ('AUD_SGD', 'CURRENCY', 'AUD/SGD'),
  ('EUR_JPY', 'CURRENCY', 'EUR/JPY'),
  ('EUR_TRY', 'CURRENCY', 'EUR/TRY'),
  ('USD_JPY', 'CURRENCY', 'USD/JPY'),
  ('BTC_USD', 'CFD', 'Bitcoin'),
  ('SGD_JPY', 'CURRENCY', 'SGD/JPY'),
  ('GBP_ZAR', 'CURRENCY', 'GBP/ZAR'),
  ('XAG_JPY', 'METAL', 'Silver/JPY'),
  ('ETH_USD', 'CFD', 'Ether'),
  ('ZAR_JPY', 'CURRENCY', 'ZAR/JPY'),
  ('AUD_JPY', 'CURRENCY', 'AUD/JPY'),
  ('SGD_CHF', 'CURRENCY', 'SGD/CHF'),
  ('CORN_USD', 'CFD', 'Corn'),
  ('EUR_CHF', 'CURRENCY', 'EUR/CHF'),
  ('NZD_CAD', 'CURRENCY', 'NZD/CAD'),
  ('USD_CNH', 'CURRENCY', 'USD/CNH'),
  ('XAU_SGD', 'METAL', 'Gold/SGD'),
  ('USD_TRY', 'CURRENCY', 'USD/TRY'),
  ('GBP_JPY', 'CURRENCY', 'GBP/JPY'),
  ('SPX500_USD', 'CFD', 'US SPX 500'),
  ('EUR_SGD', 'CURRENCY', 'EUR/SGD'),
  ('AUD_USD', 'CURRENCY', 'AUD/USD'),
  ('XCU_USD', 'CFD', 'Copper'),
  ('USB02Y_USD', 'CFD', 'US 2Y T-Note'),
  ('LTC_USD', 'CFD', 'Litecoin'),
  ('HK33_HKD', 'CFD', 'Hong Kong 33'),
  ('USD_NOK', 'CURRENCY', 'USD/NOK'),
  ('XAG_EUR', 'METAL', 'Silver/EUR'),
  ('NZD_SGD', 'CURRENCY', 'NZD/SGD'),
  ('XAG_GBP', 'METAL', 'Silver/GBP'),
  ('USD_CAD', 'CURRENCY', 'USD/CAD'),
  ('USB10Y_USD', 'CFD', 'US 10Y T-Note'),
  ('EU50_EUR', 'CFD', 'Europe 50'),
  ('EUR_AUD', 'CURRENCY', 'EUR/AUD'),
  ('TRY_JPY', 'CURRENCY', 'TRY/JPY'),
  ('XAU_NZD', 'METAL', 'Gold/NZD'),
  ('CAD_JPY', 'CURRENCY', 'CAD/JPY'),
  ('USD_ZAR', 'CURRENCY', 'USD/ZAR'),
  ('NL25_EUR', 'CFD', 'Netherlands 25'),
  ('XAU_XAG', 'METAL', 'Gold/Silver'),
  ('XAU_GBP', 'METAL', 'Gold/GBP'),
  ('USD_DKK', 'CURRENCY', 'USD/DKK'),
  ('AU200_AUD', 'CFD', 'Australia 200'),
  ('SOYBN_USD', 'CFD', 'Soybeans'),
  ('NAS100_USD', 'CFD', 'US Nas 100'),
  ('EUR_ZAR', 'CURRENCY', 'EUR/ZAR'),
  ('USD_PLN', 'CURRENCY', 'USD/PLN'),
  ('GBP_AUD', 'CURRENCY', 'GBP/AUD'),
  ('CHINAH_HKD', 'CFD', 'China H Shares'),
  ('NZD_USD', 'CURRENCY', 'NZD/USD'),
  ('USD_HKD', 'CURRENCY', 'USD/HKD'),
  ('XPT_USD', 'CFD', 'Platinum'),
  ('SG30_SGD', 'CFD', 'Singapore 30'),
  ('CHF_ZAR', 'CURRENCY', 'CHF/ZAR'),
  ('EUR_USD', 'CURRENCY', 'EUR/USD'),
  ('XAU_EUR', 'METAL', 'Gold/EUR'),
  ('XPD_USD', 'CFD', 'Palladium'),
  ('GBP_SGD', 'CURRENCY', 'GBP/SGD'),
  ('USD_SEK', 'CURRENCY', 'USD/SEK'),
  ('DE30_EUR', 'CFD', 'Germany 30'),
  ('USD_HUF', 'CURRENCY', 'USD/HUF'),
  ('EUR_CAD', 'CURRENCY', 'EUR/CAD'),
  ('EUR_DKK', 'CURRENCY', 'EUR/DKK'),
  ('NATGAS_USD', 'CFD', 'Natural Gas'),
  ('XAG_CAD', 'METAL', 'Silver/CAD'),
  ('JP225_USD', 'CFD', 'Japan 225'),
  ('UK10YB_GBP', 'CFD', 'UK 10Y Gilt'),
  ('AUD_CAD', 'CURRENCY', 'AUD/CAD'),
  ('USD_MXN', 'CURRENCY', 'USD/MXN'),
  ('GBP_USD', 'CURRENCY', 'GBP/USD'),
  ('XAU_CHF', 'METAL', 'Gold/CHF'),
  ('XAG_SGD', 'METAL', 'Silver/SGD'),
  ('CAD_CHF', 'CURRENCY', 'CAD/CHF'),
  ('BCO_USD', 'CFD', 'Brent Crude Oil'),
  ('AUD_NZD', 'CURRENCY', 'AUD/NZD'),
  ('CAD_SGD', 'CURRENCY', 'CAD/SGD'),
  ('FR40_EUR', 'CFD', 'France 40'),
  ('USB30Y_USD', 'CFD', 'US T-Bond'),
  ('NZD_HKD', 'CURRENCY', 'NZD/HKD'),
  ('USB05Y_USD', 'CFD', 'US 5Y T-Note');
