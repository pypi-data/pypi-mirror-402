import { defineComponent as o, createElementBlock as a, openBlock as e, Fragment as i, createElementVNode as s, createBlock as d, createCommentVNode as c, renderList as h, toDisplayString as n, unref as u, withCtx as m, createTextVNode as p } from "vue";
import { ProgressIndicator as g } from "@ose/js-core";
const y = { class: "alert alert-danger" }, k = { key: 1 }, f = { key: 2 }, b = /* @__PURE__ */ o({
  __name: "BCIOSearch",
  props: {
    data: {},
    release: {},
    selectedSubStep: {}
  },
  emits: ["release-control"],
  setup(t) {
    return (S, r) => (e(), a(i, null, [
      r[1] || (r[1] = s("h3", null, "Publishing the release", -1)),
      t.release.state === "waiting-for-user" && t.data?.errors?.length > 0 ? (e(!0), a(i, { key: 0 }, h(t.data.errors, (l) => (e(), a("div", y, [
        l.details && l?.response?.["hydra:description"] ? (e(), a(i, { key: 0 }, [
          s("h4", null, n(l.response["hydra:title"]), 1),
          s("p", null, n(l.details), 1),
          s("p", null, n(l.response["hydra:description"]), 1)
        ], 64)) : (e(), a("pre", k, n(JSON.stringify(l, void 0, 2)), 1))
      ]))), 256)) : (e(), d(u(g), {
        key: 1,
        details: t.data,
        release: t.release
      }, {
        default: m(() => [...r[0] || (r[0] = [
          s("p", null, [
            p(" The ontologies are being published to BCIOSearch. This will take a while."),
            s("br")
          ], -1)
        ])]),
        _: 1
      }, 8, ["details", "release"])),
      t.release.state === "completed" ? (e(), a("p", f, " The ontologies were published to BCIOSearch. ")) : c("", !0)
    ], 64));
  }
});
export {
  b as BCIOSearch
};
