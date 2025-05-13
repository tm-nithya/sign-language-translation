// //webkitURL is deprecated but nevertheless
// URL = window.URL || window.webkitURL;

// var gumStream; //stream from getUserMedia()
// var recorder; //WebAudioRecorder object
// var input; //MediaStreamAudioSourceNode we'll be recording
// var encodingType; //holds selected encoding for resulting audio (file)
// var encodeAfterRecord = true; // when to encode

// // Shim for AudioContext when it's not available
// var AudioContext = window.AudioContext || window.webkitAudioContext;
// var audioContext; //new audio context to help us record

// var encodingTypeSelect = document.getElementById("encodingTypeSelect");
// var recordButton = document.getElementById("recordButton");
// var stopButton = document.getElementById("stopButton");
// var recordingsList = document.getElementById("recordingsList");
// var log = document.getElementById("log");
// var fileInput = document.querySelector("input[name='file']");

// // Add events to the buttons
// recordButton.addEventListener("click", startRecording);
// stopButton.addEventListener("click", stopRecording);

// function startRecording() {
//   console.log("startRecording() called");

//   var constraints = { audio: true, video: false };

//   navigator.mediaDevices.getUserMedia(constraints).then(function (stream) {
//     __log("getUserMedia() success, stream created, initializing WebAudioRecorder...");

//     // Create an audio context
//     audioContext = new AudioContext();

//     // Update the format
//     document.getElementById("formats").innerHTML =
//       "Format: 2 channel " +
//       encodingTypeSelect.options[encodingTypeSelect.selectedIndex].value +
//       " @ " +
//       audioContext.sampleRate / 1000 +
//       "kHz";

//     // Assign to gumStream for later use
//     gumStream = stream;

//     // Create MediaStreamAudioSourceNode
//     input = audioContext.createMediaStreamSource(stream);

//     // Get the encoding
//     encodingType = encodingTypeSelect.options[encodingTypeSelect.selectedIndex].value;

//     // Disable the encoding selector
//     encodingTypeSelect.disabled = true;

//     // Initialize the WebAudioRecorder
//     recorder = new WebAudioRecorder(input, {
//       workerDir: "{{ url_for('static', filename='js/') }}", // Dynamic static path
//       encoding: encodingType,
//       numChannels: 2,
//       onEncoderLoading: function (recorder, encoding) {
//         __log("Loading " + encoding + " encoder...");
//       },
//       onEncoderLoaded: function (recorder, encoding) {
//         __log(encoding + " encoder loaded");
//       },
//     });

//     recorder.onComplete = function (recorder, blob) {
//       __log("Encoding complete");
//       createDownloadLink(blob, recorder.encoding);
//       encodingTypeSelect.disabled = false;
//     };

//     recorder.setOptions({
//       timeLimit: 120,
//       encodeAfterRecord: encodeAfterRecord,
//       ogg: { quality: 0.5 },
//       mp3: { bitRate: 160 },
//     });

//     // Start recording
//     recorder.startRecording();
//     __log("Recording started");

//     // Update button states
//     recordButton.disabled = true;
//     stopButton.disabled = false;
//   }).catch(function (err) {
//     // Enable the record button if getUserMedia() fails
//     recordButton.disabled = false;
//     stopButton.disabled = true;
//     __log("Error: " + err.message);
//   });

//   // Disable the record button
//   recordButton.disabled = true;
//   stopButton.disabled = false;
// }

// function stopRecording() {
//   console.log("stopRecording() called");

//   // Stop microphone access
//   gumStream.getAudioTracks()[0].stop();

//   // Disable the stop button
//   stopButton.disabled = true;
//   recordButton.disabled = false;

//   // Tell the recorder to finish the recording (stop recording + encode the recorded audio)
//   recorder.finishRecording();

//   __log("Recording stopped");
// }

// function createDownloadLink(blob, encoding) {
//   var url = URL.createObjectURL(blob);
//   var au = document.createElement("audio");
//   var li = document.createElement("li");
//   var link = document.createElement("a");

//   // Add controls to the <audio> element
//   au.controls = true;
//   au.src = url;

//   // Link the <a> element to the blob
//   link.href = url;
//   link.download = new Date().toISOString() + "." + encoding;
//   link.innerHTML = "Download Recording";

//   // Automatically append the file to the hidden input for upload
//   var file = new File([blob], "recording.wav", { type: "audio/wav" });
//   var dataTransfer = new DataTransfer();
//   dataTransfer.items.add(file);
//   fileInput.files = dataTransfer.files;

//   // Add the new audio and <a> elements to the <li> element
//   li.appendChild(au);
//   li.appendChild(link);

//   // Add the <li> element to the ordered list
//   recordingsList.appendChild(li);

//   __log("Recording ready for upload");
// }

// // Helper function
// function __log(e, data) {
//   log.innerHTML += "\n" + e + " " + (data || "");
// }



function stopRecording() {
  console.log("stopRecording() called");

  // Stop microphone access
  gumStream.getAudioTracks()[0].stop();

  // Disable the stop button
  stopButton.disabled = true;
  recordButton.disabled = false;

  // Tell the recorder to finish the recording (stop recording + encode the recorded audio)
  recorder.finishRecording();

  __log("Recording stopped");
}

function createDownloadLink(blob, encoding) {
  var url = URL.createObjectURL(blob);
  var au = document.createElement("audio");
  var li = document.createElement("li");

  // Add controls to the <audio> element
  au.controls = true;
  au.src = url;

  // Add the <audio> element to the <li> element
  li.appendChild(au);

  // Add the <li> element to the ordered list
  recordingsList.appendChild(li);

  __log("Recording ready for transcription");

  // Automatically send the audio blob to the server for transcription
  sendBlobForTranscription(blob);
}

function sendBlobForTranscription(blob) {
  const formData = new FormData();
  formData.append("file", blob, "recording.wav");

  fetch("/mic", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.transcript) {
        // Display the transcript on the page
        const transcriptDiv = document.createElement("div");
        transcriptDiv.innerHTML = `
          <h4>Recognized Text:</h4>
          <p style="font-size: 18px; font-weight: bold;">${data.transcript}</p>
        `;
        recordingsList.appendChild(transcriptDiv);
      } else {
        __log("Transcription failed.");
      }
    })
    .catch((err) => {
      console.error("Error during transcription:", err);
    });
}
