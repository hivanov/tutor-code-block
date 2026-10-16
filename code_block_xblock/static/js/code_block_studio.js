/**
 * CodeBlockStudioView: Authoring modal controller for Code Block.
 */
function CodeBlockStudioView(runtime, element) {
    var $wrapper = $(element).find('.cb-studio-wrapper');
    if (!$wrapper.length) {
        $wrapper = $(element);
    }

    var $saveBtn = $wrapper.find('.cb-save-button');
    var $cancelBtn = $wrapper.find('.cb-cancel-button');
    var $statusText = $wrapper.find('.cb-save-status');
    var $textarea = $wrapper.find('#cb-raw-code');

    // Handle Tab key in code editor
    $textarea.on('keydown', function(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            var start = this.selectionStart;
            var end = this.selectionEnd;
            var val = this.value;
            this.value = val.substring(0, start) + '    ' + val.substring(end);
            this.selectionStart = this.selectionEnd = start + 4;
        }
    });

    // Save action
    $saveBtn.on('click', function(e) {
        e.preventDefault();
        $saveBtn.prop('disabled', true);
        $statusText.removeClass('cb-status-error cb-status-success').text('Saving...');

        var payload = {
            display_name: $wrapper.find('#cb-display-name').val(),
            title: $wrapper.find('#cb-title').val(),
            language: $wrapper.find('#cb-language').val(),
            theme: $wrapper.find('#cb-theme').val(),
            raw_code: $wrapper.find('#cb-raw-code').val(),
            highlight_lines_raw: $wrapper.find('#cb-highlight-lines').val(),
            line_number_start: parseInt($wrapper.find('#cb-line-start').val(), 10) || 1,
            max_height_px: parseInt($wrapper.find('#cb-max-height').val(), 10) || 0,
            line_numbers: $wrapper.find('#cb-line-numbers').is(':checked'),
            wrap_code: $wrapper.find('#cb-wrap-code').is(':checked'),
            show_copy_button: $wrapper.find('#cb-copy-button').is(':checked')
        };

        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');

        $.ajax({
            type: 'POST',
            url: handlerUrl,
            data: JSON.stringify(payload),
            contentType: 'application/json; charset=utf-8',
            dataType: 'json',
            success: function(response) {
                $statusText.addClass('cb-status-success').text('Saved successfully!');
                setTimeout(function() {
                    runtime.notify('save', {state: 'end'});
                }, 500);
            },
            error: function(xhr) {
                $saveBtn.prop('disabled', false);
                var errorMsg = 'Error saving code block';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    errorMsg = xhr.responseJSON.message;
                }
                $statusText.addClass('cb-status-error').text(errorMsg);
            }
        });
    });

    // Cancel action
    $cancelBtn.on('click', function(e) {
        e.preventDefault();
        runtime.notify('cancel', {});
    });
}
