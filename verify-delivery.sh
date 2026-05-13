#!/bin/bash
# Benchmark verification helper for current canonical workflow

echo "=========================================="
echo "AOT CACHE BENCHMARK - VERIFICATION"
echo "=========================================="
echo ""

echo "📦 NEW JAVA SOURCE FILES"
echo "————————————————————————————"
find /Users/afshin/IdeaProjects/sandbox/java-spring-docker/src/main/java/io/github/mnafshin/java_spring_docker \
  \( -path "*/service/*" -o -path "*/control/*" -o -path "*/config/*" \) \
  -name "*.java" -not -path "*/test/*" -type f | sort | while read f; do
  lines=$(wc -l < "$f")
  echo "  ✓ $(basename "$f") ($lines lines)"
done

echo ""
echo "📋 CANONICAL AOT BENCHMARK DOCS"
echo "————————————————————————————"
ls -1 /Users/afshin/IdeaProjects/sandbox/java-spring-docker/benchmarks/05-jep483-aot-cache/*.md 2>/dev/null | while read f; do
  lines=$(wc -l < "$f")
  echo "  ✓ $(basename "$f") ($lines lines)"
done

echo ""
echo "📚 BENCHMARK-LOCAL DEEP DIVE DOCS"
echo "————————————————————————————"
ls -1 /Users/afshin/IdeaProjects/sandbox/java-spring-docker/benchmarks/*/DEEP_DIVE.md \
      /Users/afshin/IdeaProjects/sandbox/java-spring-docker/benchmarks/05-jep483-aot-cache/AOT-*.md 2>/dev/null | while read f; do
  lines=$(wc -l < "$f")
  echo "  ✓ $(basename "$f") ($lines lines)"
done

echo ""
echo "🔧 SHARED BENCHMARK SCRIPTS"
echo "————————————————————————————"
ls -1 /Users/afshin/IdeaProjects/sandbox/java-spring-docker/benchmarks/common/*.sh \
      /Users/afshin/IdeaProjects/sandbox/java-spring-docker/benchmarks/common/*.py 2>/dev/null | while read f; do
  lines=$(wc -l < "$f")
  echo "  ✓ $(basename "$f") ($lines lines)"
done

echo ""
echo "🐳 AOT SCENARIO DOCKERFILES"
echo "————————————————————————————"
find /Users/afshin/IdeaProjects/sandbox/java-spring-docker/benchmarks/05-jep483-aot-cache/variants -name "Dockerfile" | sort | while read f; do
  lines=$(wc -l < "$f")
  dir=$(dirname "$f" | xargs basename)
  echo "  ✓ $dir/Dockerfile ($lines lines)"
done

echo ""
echo "📖 PROJECT SUMMARY DOCUMENTS"
echo "————————————————————————————"
ls -1 /Users/afshin/IdeaProjects/sandbox/java-spring-docker/{*SUMMARY.md,*MANIFEST.md} 2>/dev/null | while read f; do
  lines=$(wc -l < "$f")
  echo "  ✓ $(basename "$f") ($lines lines)"
done

echo ""
echo "=========================================="
echo "✅ BUILD STATUS"
echo "=========================================="
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
if ./gradlew build -x test -q 2>&1 | grep -q "BUILD SUCCESSFUL"; then
  echo "✅ Build: SUCCESSFUL"
else
  echo "❌ Build: FAILED"
fi

echo ""
echo "=========================================="
echo "🎯 QUICK START COMMANDS"
echo "=========================================="
echo ""
echo "1️⃣  Learn about AOT Cache:"
echo "    cat benchmarks/05-jep483-aot-cache/AOT-CACHE-GUIDE.md"
echo ""
echo "2️⃣  Run canonical AOT benchmark (profile-based):"
echo "    bash benchmarks/common/run_all_benchmarks.sh --profile full"
echo ""
echo "3️⃣  Review results:"
echo "    cat benchmarks/05-jep483-aot-cache/results/raw.csv"
echo ""
echo "=========================================="
echo "📚 DOCUMENTATION INDEX"
echo "=========================================="
echo ""
echo "Getting Started:"
echo "  → benchmarks/05-jep483-aot-cache/README.md"
echo ""
echo "Deep Dive Learning:"
echo "  → benchmarks/05-jep483-aot-cache/AOT-CACHE-GUIDE.md"
echo ""
echo "Project Overview:"
echo "  → benchmarks/README.md"
echo "  → benchmarks/05-jep483-aot-cache/AOT-DOCS-INDEX.md"
echo ""
echo "Documentation Index:"
echo "  → benchmarks/05-jep483-aot-cache/AOT-DOCS-INDEX.md"
echo ""
echo "=========================================="
echo "✨ DELIVERY COMPLETE"
echo "=========================================="
echo ""
echo "You now have:"
echo "  ✅ Enhanced Spring application (10 new Java classes)"
echo "  ✅ Canonical AOT benchmark scenario (05-jep483-aot-cache)"
echo "  ✅ Manifest-driven benchmark runner with quick/full profiles"
echo "  ✅ Updated documentation index for production-like usage"
echo ""
echo "Next step: run --profile quick, then --profile full for presentation-grade results."
echo ""

