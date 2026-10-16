/**
 * CodeBlockStudentView: Client-side logic for Code Block component.
 * Handles clipboard copying, feedback tooltips, and responsive layout.
 */
function CodeBlockStudentView(runtime, element, init_args) {
    var $card = $(element).find('.cb-card');
    if (!$card.length) {
        $card = $(element);
    }

    var $copyBtn = $card.find('.cb-copy-btn');
    var $rawSource = $card.find('.cb-raw-source');
    var $copyText = $card.find('.cb-copy-text');

    if ($copyBtn.length) {
        $copyBtn.on('click', function(e) {
            e.preventDefault();

            var textToCopy = "";
            if ($rawSource.length) {
                textToCopy = $rawSource.val();
            } else {
                var $codeLines = $card.find('.cb-code-line');
                if ($codeLines.length) {
                    textToCopy = $codeLines.map(function() {
                        return $(this).text();
                    }).get().join('\n');
                } else {
                    textToCopy = $card.find('code').text();
                }
            }

            copyToClipboard(textToCopy, function(success) {
                if (success) {
                    $copyBtn.addClass('cb-copied');
                    $copyText.text('Copied!');
                    setTimeout(function() {
                        $copyBtn.removeClass('cb-copied');
                        $copyText.text('Copy');
                    }, 2000);
                }
            });
        });
    }

    function copyToClipboard(text, callback) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(function() {
                callback(true);
            }).catch(function(err) {
                fallbackCopy(text, callback);
            });
        } else {
            fallbackCopy(text, callback);
        }
    }

    function fallbackCopy(text, callback) {
        try {
            var textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-999999px";
            textArea.style.top = "-999999px";
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            var successful = document.execCommand('copy');
            document.body.removeChild(textArea);
            callback(successful);
        } catch (err) {
            console.error('CodeBlock: fallback copy failed', err);
            callback(false);
        }
    }
}
