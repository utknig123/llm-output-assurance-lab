# Summarise a Hadoop Streaming tally (kind, name, count).
# Usage: Rscript score_summary.R ../hadoop/tally.tsv
args <- commandArgs(trailingOnly = TRUE)
path <- if (length(args)) args[[1]] else "../hadoop/tally.tsv"
tally <- read.delim(path, header = FALSE, col.names = c("kind", "name", "count"), stringsAsFactors = FALSE)

decisions <- tally[tally$kind == "decision", ]
n <- sum(decisions$count)
blocked <- sum(decisions$count[decisions$name == "blocked"])
rate <- if (n > 0) blocked / n else NA

# Wilson interval for the blocked-decision rate.
z <- 1.96
if (n > 0) {
  centre <- (blocked + z^2 / 2) / (n + z^2)
  margin <- z * sqrt((blocked * (n - blocked) / n + z^2 / 4) / n) / (n + z^2)
  lo <- max(0, centre - margin)
  hi <- min(1, centre + margin)
} else {
  lo <- NA
  hi <- NA
}

scores <- tally[tally$kind == "score_sum", ]
score_n <- sum(scores$count)
score_mean <- if (score_n > 0) sum(as.numeric(scores$name) * scores$count) / score_n else NA

cat(sprintf("decisions=%d blocked=%d blocked_rate=%.3f wilson95=[%.3f, %.3f] mean_score=%.1f\n",
            n, blocked, rate, lo, hi, score_mean))
write.csv(
  data.frame(decisions = n, blocked = blocked, blocked_rate = rate,
             wilson_lo = lo, wilson_hi = hi, mean_score = score_mean),
  file = "score_summary.csv",
  row.names = FALSE
)
