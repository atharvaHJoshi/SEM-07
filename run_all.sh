#!/usr/bin/env bash
# ---------------------------------------------------------------
#  Runs all practicals of the LP-IV schedule (CSDF + IR).
#
#  Usage:
#    ./run_all.sh          -> run everything
#    ./run_all.sh csdf     -> only CSDF practicals + CSDF mini project
#    ./run_all.sh ir       -> only IR practicals
#    ./run_all.sh project  -> only the IR mini-project (document summarizer)
#    ./run_all.sh csdf-project -> only the CSDF mini-project (image forensics)
# ---------------------------------------------------------------

cd "$(dirname "$0")" || exit 1

WHICH="${1:-all}"

section() {
    echo
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
}

run() {
    echo "\$ python3 $*"
    echo
    python3 "$@"
    status=$?
    if [ $status -ne 0 ]; then
        echo
        echo "!! this script exited with error code $status"
    fi
}

run_csdf_mini_project() {
    section "CSDF Mini Project : Digital Image Forensics Tool"
    echo "\$ CSDF/MiniProject_Image_Forensics/run_demo.sh"
    echo
    CSDF/MiniProject_Image_Forensics/run_demo.sh
    status=$?
    if [ $status -ne 0 ]; then
        echo
        echo "!! this script exited with error code $status"
    fi
}

run_csdf() {
    section "CSDF Practical 1 : Track Emails / Analyse Email Header"
    run "CSDF/Practical1_Email_Header_Analysis/email_header_analysis.py"

    section "CSDF Practical 2 : Generate and Verify CAPTCHA Image"
    if python3 -c "import PIL" 2>/dev/null; then
        if [ -t 0 ]; then
            # running in a terminal -> you can type the CAPTCHA answer
            python3 CSDF/Practical2_CAPTCHA/captcha.py
        else
            # not a terminal -> give dummy answers automatically
            printf 'TEST\nTEST\nTEST\n' | python3 CSDF/Practical2_CAPTCHA/captcha.py
        fi
    else
        echo "Pillow is not installed, so this practical cannot run."
        echo "Install it with:  pip install pillow   (or: sudo pacman -S python-pillow)"
    fi

    section "CSDF Practical 3 : Detect WiFi Password-Cracking Attempt"
    run "CSDF/Practical3_WiFi_Intrusion_Detection/wifi_intrusion_detection.py"

    run_csdf_mini_project
}

run_ir() {
    section "IR Practical 1 : Similarity Between Two Text Documents"
    run "IR/Practical1_Document_Similarity/document_similarity.py"

    section "IR Practical 2 : PageRank Algorithm"
    run "IR/Practical2_PageRank/pagerank.py"

    section "IR Practical 3 : Map-Reduce Alphabetic Character Count"
    run "IR/Practical3_MapReduce_Character_Count/map_reduce_char_count.py"

    section "IR Practical 4 : Simple Web Crawler"
    run "IR/Practical4_Web_Crawler/web_crawler.py"

    section "IR Practical 5 : XML Web Graph + Topic Specific PageRank"
    run "IR/Practical5_XML_WebGraph_Topic_PageRank/xml_topic_pagerank.py"
}

run_project() {
    section "IR Mini Project : Document Summarization System"
    run "IR/MiniProject_Document_Summarization/summarizer.py"
}

run_csdf_project() {
    run_csdf_mini_project
}

case "$WHICH" in
    csdf)          run_csdf ;;
    csdf-project)  run_csdf_project ;;
    ir)            run_ir ;;
    project)       run_project ;;
    all)           run_csdf; run_ir; run_project ;;
    *)             echo "usage: $0 [csdf|csdf-project|ir|project|all]"; exit 1 ;;
esac

echo
echo "============================================================"
echo "  All done!"
echo "============================================================"
