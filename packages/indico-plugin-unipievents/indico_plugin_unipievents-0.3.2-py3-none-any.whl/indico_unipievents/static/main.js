function disableSyncButton() {
    let el = document.getElementById('wp-sync-button');
    el.innerHTML = WPSYNC_CONFIG.INPROGRESS_TEXT;
    el.onclick = undefined;
}

function enableSyncButton() {
    // Try to see if we can actually find the seminar inside the database
    updateLink()
}

async function updateLink() {
    let el = document.getElementById('wp-sync-button');
    el.href = `https://manage.dm.unipi.it/process/seminars/add/?prefill=indico:${eventID}`

    let info = document.getElementById('manage-info')

    const res = await fetch(`https://manage.dm.unipi.it/api/v0/public/seminars/?externalid=indico:${eventID}`)
    const data = await res.json()

    if (data.data.length > 0) {
        // We actually have an event already
        const event = data.data[0]
        el.href = `https://manage.dm.unipi.it/process/seminars/add/${event._id}?prefill=indico:${eventID}`

        info.innerHTML = "<span style='color: green;'>&#10004;</span> Il seminario / conferenza è già presente sul sito di dipartimento: il bottone sotto permette di aggiornare i dati."
    }
    else {
        info.innerHTML = "<span style='color: red;'>&#10008;</span> Il seminario / conferenza non è presente sul sito di dipartimento."
    }
}

async function onWordpressSync(event) {
}

window.addEventListener('DOMContentLoaded', enableSyncButton);

