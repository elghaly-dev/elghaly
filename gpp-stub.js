/*
 * IAB Tech Lab Global Privacy Platform (GPP) CMP API for elghaly.dev
 * Spec: CMP API v1.1 (InteractiveAdvertisingBureau/Global-Privacy-Platform,
 * Core/CMP API Specification.md; v1.1 = upstream PR #70).
 *
 * A small self-hosted, complete implementation (answers at once, no queue):
 *  - no GPP section applies on this site, so applicableSections is [-1],
 *    sectionList and supportedAPIs are empty, and the GPP string is the
 *    header-only string "DBAA" (Type 3, Version 1, zero section IDs).
 *  - cmpId is 1: the spec's value for parties that are not registered CMPs.
 *  - v1.1 rules: __gpp() returns nothing; every command answers through
 *    callback(data, success); there is no getGPPData command.
 *  - a hidden "__gppLocator" iframe and a postMessage handler let scripts in
 *    child frames call the API.
 * It does not read or change the Google Consent Mode banner or its storage.
 */
(function (w, d) {
  'use strict';
  // If another GPP CMP (or its stub) is already on the page, leave it in charge.
  if (typeof w.__gpp === 'function') return;

  var GPP_STRING = 'DBAA';
  var listeners = {};
  var lastId = 0;

  function pingData() {
    return {
      gppVersion: '1.1',
      cmpStatus: 'loaded',
      cmpDisplayStatus: 'disabled', // no GPP layer will show: no section applies
      signalStatus: 'ready',
      supportedAPIs: [],
      cmpId: 1,
      sectionList: [],
      applicableSections: [-1],
      gppString: GPP_STRING,
      parsedSections: {}
    };
  }

  function call(cb, data, success) {
    try { cb(data, success); } catch (e) {
      if (w.console && console.error) console.error('__gpp callback error', e);
    }
  }

  function gpp(command, callback, parameter /*, version */) {
    if (typeof callback !== 'function') return;
    switch (command) {
      case 'ping':
        call(callback, pingData(), true);
        break;
      case 'addEventListener':
        lastId += 1;
        listeners[lastId] = callback;
        call(callback, {
          eventName: 'listenerRegistered',
          listenerId: lastId,
          data: true,
          pingData: pingData()
        }, true);
        break;
      case 'removeEventListener':
        var id = Number(parameter);
        var removed = Object.prototype.hasOwnProperty.call(listeners, id);
        if (removed) delete listeners[id];
        call(callback, removed, true);
        break;
      case 'hasSection':
        call(callback, false, true);
        break;
      case 'getSection':
      case 'getField':
        call(callback, null, true);
        break;
      default:
        // Unknown or section-specific command: no section is supported here.
        call(callback, null, false);
    }
  }

  w.__gpp = gpp;

  w.addEventListener('message', function (event) {
    var isString = typeof event.data === 'string';
    var json = null;
    if (isString) {
      if (event.data.indexOf('__gppCall') === -1) return;
      try { json = JSON.parse(event.data); } catch (e) { return; }
    } else {
      json = event.data;
    }
    if (!json || typeof json !== 'object' || !json.__gppCall) return;
    var c = json.__gppCall;
    if (!event.source || typeof event.source.postMessage !== 'function') return;
    gpp(c.command, function (returnValue, success) {
      var msg = { __gppReturn: { returnValue: returnValue, success: success, callId: c.callId } };
      event.source.postMessage(isString ? JSON.stringify(msg) : msg, '*');
    }, 'parameter' in c ? c.parameter : null, c.version || '1.1');
  }, false);

  function addFrame() {
    if (w.frames.__gppLocator) return;
    if (d.body) {
      var f = d.createElement('iframe');
      f.style.cssText = 'display:none';
      f.name = '__gppLocator';
      f.title = 'GPP locator';
      f.setAttribute('aria-hidden', 'true');
      f.tabIndex = -1;
      d.body.appendChild(f);
    } else {
      setTimeout(addFrame, 10);
    }
  }
  addFrame();
})(window, document);
