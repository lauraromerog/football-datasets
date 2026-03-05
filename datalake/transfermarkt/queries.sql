CREATE VIEW IF NOT EXISTS v_market_value_positions AS
SELECT
    h.player_id,
    CAST(strftime('%Y', h.date_unix) AS INTEGER)    AS value_year,
    h.value / 1000000.0                             AS value_m,
    p.position,
    p.main_position,
    p.foot
FROM player_market_value h
INNER JOIN player_profiles p ON h.player_id = p.player_id
WHERE
    h.value IS NOT NULL
    AND h.value > 0
    AND p.position != ''
    AND p.main_position != ''
    AND p.foot!= ''
    AND (p.main_position != p.position OR p.main_position = 'Goalkeeper')
    AND CAST(strftime('%Y', h.date_unix) AS INTEGER) BETWEEN 2015 AND 2025;

-- which positions have the highest average market value across all years?
SELECT
    main_position,
    position AS position_group,
    ROUND(AVG(value_m), 2) AS avg_value_m,
    ROUND(MAX(value_m), 2) AS max_value_m,
    ROUND(MIN(value_m), 2) AS min_value_m,
    COUNT(DISTINCT player_id) AS unique_players
FROM v_market_value_positions
GROUP BY main_position, position_group
ORDER BY avg_value_m DESC;

-- Has it shifted? — avg value per main position 
SELECT main_position,
    CASE
        WHEN value_year BETWEEN 2015 AND 2017 THEN '2015-2017'
        WHEN value_year BETWEEN 2018 AND 2020 THEN '2018-2020'
        WHEN value_year BETWEEN 2021 AND 2025 THEN '2021-2025'
    END AS period,
    ROUND(AVG(value_m), 2) AS avg_value_m,
    COUNT(DISTINCT player_id)AS unique_players
FROM v_market_value_positions
GROUP BY main_position, period
ORDER BY main_position, period;

--How has the overall transfer market inflated season by season? Are fees growing faster than market values?
SELECT season_name  AS season, ROUND(AVG(transfer_fee) / 1000000.0, 2) AS avg_fee_m, ROUND(SUM(transfer_fee) / 1000000.0, 2) AS total_fee_m, COUNT(*) AS num_transfers
FROM transfer_history
WHERE transfer_fee IS NOT NULL AND transfer_fee > 0
GROUP BY season_name
ORDER BY season_name;
SELECT CAST(strftime('%Y', date_unix) AS INTEGER) AS season, ROUND(AVG(value) / 1000000.0, 2) AS avg_market_value_m
FROM player_market_value
WHERE value IS NOT NULL AND value > 0
GROUP BY season
ORDER BY season;
WITH fee_by_season AS (SELECT CAST(strftime('%Y', transfer_date) AS INTEGER)  AS season, ROUND(AVG(transfer_fee) / 1000000.0, 2) AS avg_fee_m
    FROM transfer_history
    WHERE transfer_fee IS NOT NULL AND transfer_fee > 0
    GROUP BY season),value_by_season AS (SELECT CAST(strftime('%Y', date_unix) AS INTEGER) AS season, ROUND(AVG(value) / 1000000.0, 2) AS avg_market_value_m
    FROM player_market_value
    WHERE value IS NOT NULL AND value > 0
    GROUP BY season)
SELECT f.season,  f.avg_fee_m, v.avg_market_value_m, ROUND((f.avg_fee_m - v.avg_market_value_m) / v.avg_market_value_m * 100, 1) AS fee_premium_pct
FROM fee_by_season f
INNER JOIN value_by_season v ON f.season = v.season
ORDER BY f.season;


-- scouting efficiency when buying
SELECT t.to_team_name,d.competition_id AS league, COUNT(t.player_id) AS transfers_in, ROUND(ABS(AVG((t.transfer_fee - t.value_at_transfer) * 1.0 / t.value_at_transfer * 100)), 2) AS avg_buy_discount_pct
FROM transfer_history t
INNER JOIN team_details d ON t.to_team_id = d.club_id
WHERE d.competition_id IN ('ES1', 'GB1', 'FR1', 'L1', 'IT1')  AND t.transfer_fee > 0  AND t.value_at_transfer > 0
GROUP BY t.to_team_id, t.to_team_name, d.competition_id   -- anchor on ID, not just name
HAVING AVG( (t.transfer_fee - t.value_at_transfer) * 1.0 / t.value_at_transfer * 100 ) < 0 AND COUNT(t.player_id) > 10
ORDER BY avg_buy_discount_pct DESC
LIMIT 15;

-- scouting efficiency when selling
SELECT t.from_team_name, d.competition_id AS league, COUNT(t.player_id) AS transfers_out, ROUND(AVG((t.transfer_fee - t.value_at_transfer) * 1.0/ t.value_at_transfer * 100), 2) AS avg_sell_premium_pct
FROM transfer_history t
INNER JOIN team_details d ON t.from_team_id = d.club_id
WHERE d.competition_id IN ('ES1', 'GB1', 'FR1', 'L1', 'IT1') AND t.transfer_fee > 0 AND t.value_at_transfer > 0
GROUP BY t.from_team_id, t.from_team_name, d.competition_id
HAVING AVG((t.transfer_fee - t.value_at_transfer) * 1.0/ t.value_at_transfer * 100) > 0 AND COUNT(t.player_id) > 10
ORDER BY avg_sell_premium_pct DESC
LIMIT 15;

--Does a high transfer fee actually translate into better performance
WITH player_perf AS (SELECT player_id, SUM(goals) AS total_goals, SUM(assists) AS total_assists, SUM(minutes_played) AS total_minutes FROM player_performances GROUP BY player_id),transfer_quartiles AS (
SELECT t.player_id, t.transfer_fee, NTILE(4) OVER (ORDER BY t.transfer_fee) AS fee_quartile FROM transfer_history t INNER JOIN team_details d ON t.to_team_id = d.club_id
WHERE d.competition_id IN ('ES1', 'GB1', 'FR1', 'L1', 'IT1') AND t.transfer_fee > 0 AND t.value_at_transfer > 0)
SELECT tq.fee_quartile, COUNT(tq.player_id) AS player_count, ROUND(AVG(pp.total_goals), 2) AS avg_goals, ROUND(AVG(pp.total_assists), 2) AS avg_assists, ROUND(AVG(pp.total_minutes), 2) AS avg_minutes
FROM transfer_quartiles tq
INNER JOIN player_perf pp ON tq.player_id  = pp.player_id
INNER JOIN player_profiles prof ON tq.player_id  = prof.player_id
WHERE prof.main_position != 'Goalkeeper'
GROUP BY tq.fee_quartile
ORDER BY tq.fee_quartile;


--Which nationalities command a premium market value
WITH top_countries AS (SELECT country_of_birth 
FROM player_profiles WHERE country_of_birth IS NOT NULL 
GROUP BY country_of_birth 
ORDER BY COUNT(*) DESC
LIMIT 20),
premiums AS (
    SELECT prof.country_of_birth, t.transfer_fee * 1.0 / t.value_at_transfer AS fee_premium_ratio
    FROM transfer_history t
    INNER JOIN player_profiles prof ON t.player_id = prof.player_id
    INNER JOIN top_countries tc ON prof.country_of_birth = tc.country_of_birth
    WHERE t.transfer_fee > 0
      AND t.value_at_transfer > 0
      AND t.transfer_fee IS NOT NULL
      AND t.value_at_transfer IS NOT NULL)
SELECT
    country_of_birth,
    COUNT(*) AS player_count,
    ROUND(AVG(fee_premium_ratio), 3) AS avg_premium_ratio,
    ROUND(MIN(fee_premium_ratio), 3) AS min_ratio,
    ROUND(MAX(fee_premium_ratio), 3) AS max_ratio
FROM premiums
GROUP BY country_of_birth
ORDER BY avg_premium_ratio DESC;

--How does a player's market value evolve after moving to a bigger or smaller league?
WITH transfer_leagues AS (
    SELECT t.player_id, t.transfer_date, t.value_at_transfer, t.from_team_id, t.to_team_id, d_from.competition_id AS from_league, d_to.competition_id AS to_league
    FROM transfer_history t
    LEFT JOIN team_details d_from ON t.from_team_id = d_from.club_id
    LEFT JOIN team_details d_to   ON t.to_team_id   = d_to.club_id
    WHERE t.value_at_transfer > 0 AND t.value_at_transfer IS NOT NULL),
classified AS (SELECT *,
        CASE
            WHEN from_league NOT IN ('ES1','GB1','FR1','L1','IT1') AND to_league IN ('ES1','GB1','FR1','L1','IT1') THEN 'step_up'
            WHEN from_league IN ('ES1','GB1','FR1','L1','IT1') AND to_league NOT IN ('ES1','GB1','FR1','L1','IT1') THEN 'step_down'
        END AS move_type
    FROM transfer_leagues
    WHERE from_league IS NOT NULL AND to_league IS NOT NULL),
with_next_value AS (SELECT *, LEAD(value_at_transfer) OVER (PARTITION BY player_id ORDER BY transfer_date) AS next_value
    FROM classified
    WHERE move_type IS NOT NULL)
SELECT move_type,COUNT(*) AS player_count, ROUND(AVG((next_value - value_at_transfer) * 1.0/ value_at_transfer * 100), 2) AS avg_value_change_pct
FROM with_next_value
WHERE next_value IS NOT NULL AND next_value > 0
GROUP BY move_type
ORDER BY move_type;

-- Do players with more international caps have a higher market value? 
WITH active_players AS (SELECT player_id FROM player_profiles WHERE current_club_name NOT IN ('Retired', '---', '0')AND current_club_name IS NOT NULL),
national_caps AS (SELECT player_id, SUM(matches) AS total_caps
    FROM player_national_performances
    WHERE career_state = 'CURRENT_NATIONAL_PLAYER' AND matches > 0
    GROUP BY player_id), market_values AS (SELECT p.player_id,
        CASE
            WHEN lmv.value > 0 AND lmv.value IS NOT NULL THEN lmv.value
            WHEN mv.value > 0 AND mv.value  IS NOT NULL THEN mv.value
            ELSE NULL
        END AS market_value
    FROM active_players p
    LEFT JOIN player_latest_market_value lmv ON p.player_id = lmv.player_id
    LEFT JOIN player_market_value        mv  ON p.player_id = mv.player_id)
SELECT
    CASE
        WHEN nc.total_caps BETWEEN 1  AND 10  THEN '1–10'
        WHEN nc.total_caps BETWEEN 11 AND 50  THEN '11–50'
        ELSE '50+'
    END AS cap_bucket,
    COUNT(*) AS player_count,
    ROUND(AVG(mv.market_value)) AS avg_market_value
FROM national_caps nc
INNER JOIN market_values mv ON nc.player_id = mv.player_id
WHERE mv.market_value IS NOT NULL AND nc.total_caps > 0
GROUP BY cap_bucket
ORDER BY cap_bucket;