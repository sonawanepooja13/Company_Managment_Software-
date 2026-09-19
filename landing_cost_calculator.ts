/**
 * Landing Cost Calculator
 * =======================
 * Calculates the true cost of importing goods from China to India.
 *
 * Formula:
 *   CIF_base       = Procurement_INR + Freight_INR + PortCharges_INR
 *   BCD            = CIF_base × (BCD_Rate / 100)
 *   SWS            = (CIF_base + BCD) × (SWS_Rate / 100)
 *   IGST           = (CIF_base + BCD + SWS) × (IGST_Rate / 100)
 *   LandingCost    = CIF_base + BCD + SWS + IGST
 *
 * All amounts are in INR. Procurement is converted from USD/CNY using
 * the exchange rate effective on the invoice date.
 */

/* ------------------------------------------------------------------ */
/* PostgreSQL function for landing cost calculation                    */
/* ------------------------------------------------------------------ */

CREATE OR REPLACE FUNCTION calculate_landing_cost(
    p_procurement_usd     NUMERIC,
    p_procurement_cny     NUMERIC,
    p_invoice_currency    CHAR(3),
    p_exchange_rate       NUMERIC,        -- USD→INR or CNY→INR on invoice date
    p_freight_inr         NUMERIC,
    p_port_charges_inr    NUMERIC,
    p_bcd_rate            NUMERIC,        -- e.g. 10.0 for 10%
    p_sws_rate            NUMERIC,        -- e.g. 10.0 for 10%
    p_igst_rate           NUMERIC
)
RETURNS TABLE (
    procurement_inr   NUMERIC,
    cif_base_inr      NUMERIC,
    bcd_amount_inr    NUMERIC,
    sws_amount_inr    NUMERIC,
    igst_amount_inr   NUMERIC,
    total_landing_cost NUMERIC
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_procurement_inr NUMERIC;
    v_cif_base        NUMERIC;
    v_bcd             NUMERIC;
    v_sws             NUMERIC;
    v_igst            NUMERIC;
    v_total           NUMERIC;
BEGIN
    -- Convert procurement cost to INR based on invoice currency
    IF p_invoice_currency = 'USD' THEN
        v_procurement_inr := p_procurement_usd * p_exchange_rate;
    ELSIF p_invoice_currency = 'CNY' THEN
        v_procurement_inr := p_procurement_cny * p_exchange_rate;
    ELSE
        v_procurement_inr := p_procurement_usd * p_exchange_rate; -- fallback
    END IF;

    -- CIF base = Procurement + Freight + Port Charges
    v_cif_base := v_procurement_inr + p_freight_inr + p_port_charges_inr;

    -- Basic Customs Duty
    v_bcd := v_cif_base * (p_bcd_rate / 100);

    -- Social Welfare Surcharge (on CIF + BCD)
    v_sws := (v_cif_base + v_bcd) * (p_sws_rate / 100);

    -- Integrated GST (on CIF + BCD + SWS)
    v_igst := (v_cif_base + v_bcd + v_sws) * (p_igst_rate / 100);

    -- Total landing cost
    v_total := v_cif_base + v_bcd + v_sws + v_igst;

    RETURN QUERY SELECT
        ROUND(v_procurement_inr, 2),
        ROUND(v_cif_base, 2),
        ROUND(v_bcd, 2),
        ROUND(v_sws, 2),
        ROUND(v_igst, 2),
        ROUND(v_total, 2);
END;
$$;

/* ------------------------------------------------------------------ */
/* Node.js / TypeScript implementation (for Next.js API routes)       */
/* ------------------------------------------------------------------ */

interface LandingCostInput {
  procurementUsd?: number;
  procurementCny?: number;
  invoiceCurrency: 'USD' | 'CNY';
  exchangeRate: number;       // USD→INR or CNY→INR
  freightInr: number;
  portChargesInr: number;
  bcdRate: number;            // e.g. 10 for 10%
  swsRate: number;            // e.g. 10 for 10%
  igstRate: number;            // e.g. 18 for 18%
}

interface LandingCostResult {
  procurementInr: number;
  cifBaseInr: number;
  bcdAmountInr: number;
  swsAmountInr: number;
  igstAmountInr: number;
  totalLandingCostInr: number;
}

/**
 * Calculates the true landing cost of importing goods from China to India.
 *
 * @example
 * // Procurement: ¥1000 CNY → ₹11,500 (rate 11.50)
 * // Freight: ₹8,000, Port charges: ₹1,500
 * // BCD 10%, SWS 10%, IGST 18%
 * calculateLandingCost({
 *   procurementCny: 1000,
 *   invoiceCurrency: 'CNY',
 *   exchangeRate: 11.50,
 *   freightInr: 8000,
 *   portChargesInr: 1500,
 *   bcdRate: 10,
 *   swsRate: 10,
 *   igstRate: 18,
 * });
 * // → { procurementInr: 11500, cifBaseInr: 21000, bcdAmountInr: 2100, ... }
 */
function calculateLandingCost(input: LandingCostInput): LandingCostResult {
  // Step 1: Convert procurement cost to INR
  const procurementInr =
    input.invoiceCurrency === 'CNY'
      ? (input.procurementCny || 0) * input.exchangeRate
      : (input.procurementUsd || 0) * input.exchangeRate;

  // Step 2: CIF base = Procurement + Freight + Port Charges
  const cifBaseInr = procurementInr + input.freightInr + input.portChargesInr;

  // Step 3: Basic Customs Duty (on CIF base)
  const bcdAmountInr = cifBaseInr * (input.bcdRate / 100);

  // Step 4: Social Welfare Surcharge (on CIF + BCD)
  const swsAmountInr = (cifBaseInr + bcdAmountInr) * (input.swsRate / 100);

  // Step 5: Integrated GST (on CIF + BCD + SWS)
  const igstAmountInr = (cifBaseInr + bcdAmountInr + swsAmountInr) * (input.igstRate / 100);

  // Step 6: Total landing cost
  const totalLandingCostInr = cifBaseInr + bcdAmountInr + swsAmountInr + igstAmountInr;

  return {
    procurementInr: Math.round(procurementInr * 100) / 100,
    cifBaseInr: Math.round(cifBaseInr * 100) / 100,
    bcdAmountInr: Math.round(bcdAmountInr * 100) / 100,
    swsAmountInr: Math.round(swsAmountInr * 100) / 100,
    igstAmountInr: Math.round(igstAmountInr * 100) / 100,
    totalLandingCostInr: Math.round(totalLandingCostInr * 100) / 100,
  };
}

/* ------------------------------------------------------------------ */
/* Example usage in SQL with the schema                               */
/* ------------------------------------------------------------------ */

-- Sample: Insert a landing cost calculation for a shipment
INSERT INTO landing_costs (
    product_id,
    shipment_id,
    procurement_usd,
    procurement_cny,
    invoice_currency,
    exchange_rate,
    exchange_rate_date,
    freight_inr,
    port_charges_inr,
    cif_base_inr,
    bcd_rate,
    bcd_amount_inr,
    sws_rate,
    sws_amount_inr,
    igst_rate,
    igst_amount_inr,
    total_landing_cost_inr
)
SELECT
    p.id                                AS product_id,
    s.id                                AS shipment_id,
    s.invoice_amount_usd                AS procurement_usd,
    s.invoice_amount_cny                AS procurement_cny,
    s.invoice_currency                  AS invoice_currency,
    er.rate                             AS exchange_rate,
    s.invoice_date                      AS exchange_rate_date,
    s.freight_cost_inr                  AS freight_inr,
    s.port_charges_inr                  AS port_charges_inr,
    lc.cif_base_inr,
    COALESCE(p.gst_slab * 0.75, 7.5)    AS bcd_rate,      -- typical BCD = 75% of GST slab
    lc.bcd_amount_inr,
    10.0                                AS sws_rate,       -- 10% SWS
    lc.sws_amount_inr,
    p.gst_slab                          AS igst_rate,       -- IGST = product's GST slab
    lc.igst_amount_inr,
    lc.total_landing_cost_inr
FROM products p
JOIN import_shipments s ON s.id = s.id
JOIN exchange_rates er  ON er.from_currency = s.invoice_currency AND er.to_currency = 'INR'
CROSS JOIN LATERAL calculate_landing_cost(
    s.invoice_amount_usd,
    s.invoice_amount_cny,
    s.invoice_currency,
    er.rate,
    s.freight_cost_inr,
    s.port_charges_inr,
    COALESCE(p.gst_slab * 0.75, 7.5), -- BCD rate
    10.0,                              -- SWS rate
    p.gst_slab                         -- IGST rate
) AS lc
WHERE s.id = ? AND p.id = ?;
