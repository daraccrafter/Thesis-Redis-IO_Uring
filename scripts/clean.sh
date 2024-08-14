rm -rf benchmarks/*/csvs
rm -rf benchmarks/*/logs
rm -rf graphs
rm -rf benchmarks/*/temp
rm -rf benchmarks/*/data
rm -rf benchmarks/URING_AOF/temp-integrity
rm -rf persistance-data
rm -rf benchmarks/__pycache__
./script-cleanup.sh
rm -f verify_incr_log.csv
rm -f verify_keys_log.csv
rm -f verify_samekey_log.csv
