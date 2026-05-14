#!/usr/bin/env bash
# Load testing script for AOT cache warm-up
# Demonstrates realistic workload during cache training

set -euo pipefail

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8080}"
NUM_REQUESTS="${NUM_REQUESTS:-100}"
CONCURRENT="${CONCURRENT:-5}"

echo "==========================================="
echo "AOT Cache Complex Benchmark - Load Generator"
echo "==========================================="
echo "URL: $BASE_URL"
echo "Requests: $NUM_REQUESTS"
echo "Concurrent: $CONCURRENT"
echo ""

# Wait for app ready
wait_for_app() {
    local max_attempts=60
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$BASE_URL/actuator/health/readiness" > /dev/null 2>&1; then
            echo "✓ Application is ready"
            return 0
        fi

        echo "Waiting for application... ($((attempt+1))/$max_attempts)"
        sleep 1
        ((attempt++))
    done

    echo "✗ Application failed to start"
    return 1
}

# Generate load to populate reflection caches
generate_load() {
    echo ""
    echo "Generating load to populate reflection caches..."

    local endpoints=(
        "/api/products"
        "/api/products/active"
        "/api/products/category/Electronics"
        "/api/products/search?q=laptop"
        "/api/users"
        "/api/info"
        "/api/status"
        "/bench/read"
        "/bench/cpu?work=5000"
    )

    local request_count=0

    # Sequential requests
    for ((i=0; i<NUM_REQUESTS; i++)); do
        endpoint="${endpoints[$((i % ${#endpoints[@]}))]}"

        # Make request in background (up to CONCURRENT limit)
        (
            response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
            http_code=$(echo "$response" | tail -n1)

            if [ "$http_code" = "200" ]; then
                echo "✓ Request $((i+1)): $endpoint"
            else
                echo "✗ Request $((i+1)): $endpoint (HTTP $http_code)"
            fi
        ) &

        # Limit concurrent requests
        if [ $(jobs -r -p | wc -l) -ge $CONCURRENT ]; then
            wait -n
        fi

        ((request_count++))
    done

    # Wait for remaining jobs
    wait

    echo ""
    echo "✓ Generated $request_count requests"
}

# Main execution
main() {
    if ! wait_for_app; then
        exit 1
    fi

    generate_load

    echo ""
    echo "==========================================="
    echo "Load generation complete"
    echo "==========================================="
}

main "$@"

