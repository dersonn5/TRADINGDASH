-- Prova Zero7: plano de 16/11/2026 (decisao do operador com a prova em -R$ 3.552 em 16 trades).
-- 3 trades no dia e 2 stops seguidos encerram (eram 5 e 3).
-- As cotas por hora da prova (sem 1a hora, 2 trades as 10h, 1 a partir das 11:30) ficam no
-- codigo: lib/prova.ts, REGRAS_DA_HORA_PROVA. Pode rodar de novo.

UPDATE copa_contas
   SET max_perdas_seguidas = 2,
       max_operacoes_dia   = 3
 WHERE tipo = 'PROVA';

-- Conferencia: a prova com 2 e 3, a conta real com 3 e 5
SELECT nome, tipo, max_contratos, max_risco_trade_rs, max_perdas_seguidas, max_operacoes_dia
  FROM copa_contas
 ORDER BY tipo DESC;
