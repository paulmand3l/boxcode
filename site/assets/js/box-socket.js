var wsuri = "ws://10.0.1.84:9000";

var devices = {};

function createBox(topicUri, device) {
    console.log('Creating Servo');
    var box = $('.device.prototype').clone()
                .removeClass('.prototype')
                .button()
                .css({'display': 'block'});
    $('.graph').append(box);
    devices[device.id] = box;
}

function detachBox(topicUri, device) {
    console.log('Destroying Servo');
    var box = devices[device.id];
    box.remove();
    delete devices[device.id];
}

$(function() {

    ab.connect(wsuri,
        function(session) {
            window.sess = session;
            console.log('Connected');

            window.sess.subscribe("http://mand3l.com/device/attach", onAttach);
            window.sess.subscribe('http://mand3l.com/device/detach', onDetach);
            window.sess.subscribe('http://mand3l.com/device/update', onUpdate);

            window.sess.prefix("servo", "http://mand3l.com/devices/webservo#");

            window.sess.subscribe("http://mand3l.com/device/attach", createBox);
            window.sess.subscribe("http://mand3l.com/device/detach", detachBox);
        },

        function(code, reason) {
            window.sess = undefined;
            console.log('Disconnected');
        }
    );
});

$(window).on('pageinit', function() {
    $('#servoVal').change(function(e) {
        console.log('servo:setPosition');
        window.sess.call('servo:setPosition', 0, parseInt($('#servoVal').val()));
    });
});

function onAttach(topicUri, device) {
    console.log(device.name + ' connected.');
}

function onDetach(topicUri, device) {
    console.log(device.name + ' disconnected.');
}

function onUpdate(topicUri, event) {
    console.log(device.name + ' updated to ' + event.device.value + '.');
}
