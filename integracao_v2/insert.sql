-- Gerar sequência de paradas das linhas

INSERT INTO linha_sentido_parada.tab_paradas_linhas_seq (cod_linha, sentido, paradas)
SELECT
    l.cod_linha,
    CASE 
        WHEN lower(l.dsc_sentido) = 'circular' THEN 'CIRCULAR'
        ELSE l.dsc_sentido
    END AS sentido,
    array_agg(p.id_ponto_parada ORDER BY
        ST_LineLocatePoint(
            l.geo_linhas_lin,
            ST_Transform(p.geo_point, 31983)
        )
    ) AS paradas
FROM
    linha_sentido_parada.tab_linhas l
JOIN
    linha_sentido_parada.tab_ponto_interpolado p
    ON ST_DWithin(
        ST_Transform(p.geo_point, 31983),
        l.geo_linhas_lin,
        1
    )
GROUP BY
    l.cod_linha,
    CASE 
        WHEN lower(l.dsc_sentido) = 'circular' THEN 'CIRCULAR'
        ELSE l.dsc_sentido
    END
ORDER BY
    l.cod_linha,
    sentido;