import { defineComponent as r, createElementBlock as a, openBlock as e, Fragment as o, createElementVNode as s, createBlock as d, createCommentVNode as c, renderList as u, toDisplayString as n, unref as h, withCtx as m, createTextVNode as p } from "vue";
import { ProgressIndicator as g } from "@ose/js-core";
const b = { class: "alert alert-danger" }, y = { key: 1 }, k = { key: 2 }, O = /* @__PURE__ */ r({
  __name: "AddictOVocab",
  props: {
    data: {},
    release: {},
    selectedSubStep: {}
  },
  emits: ["release-control"],
  setup(t) {
    return (f, i) => (e(), a(o, null, [
      i[1] || (i[1] = s("h3", null, "Publishing the release", -1)),
      t.release.state === "waiting-for-user" && t.data?.errors?.length > 0 ? (e(!0), a(o, { key: 0 }, u(t.data.errors, (l) => (e(), a("div", b, [
        l.details && l?.response?.["hydra:description"] ? (e(), a(o, { key: 0 }, [
          s("h4", null, n(l.response["hydra:title"]), 1),
          s("p", null, n(l.details), 1),
          s("p", null, n(l.response["hydra:description"]), 1)
        ], 64)) : (e(), a("pre", y, n(JSON.stringify(l, void 0, 2)), 1))
      ]))), 256)) : (e(), d(h(g), {
        key: 1,
        details: t.data,
        release: t.release
      }, {
        default: m(() => [...i[0] || (i[0] = [
          s("p", null, [
            p(" The ontologies are being published to AddictOVocab. This will take a while."),
            s("br")
          ], -1)
        ])]),
        _: 1
      }, 8, ["details", "release"])),
      t.release.state === "completed" ? (e(), a("p", k, " The ontologies were published to AddictOVocab. ")) : c("", !0)
    ], 64));
  }
});
export {
  O as AddictOVocab
};
