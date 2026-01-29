import unittest

from turbo_agent_core.schema.events import (
    ContentActionDeltaEvent,
    ContentActionDeltaPayload,
    ContentActionEndEvent,
    ContentActionEndPayload,
    ContentActionResultEndEvent,
    ContentActionResultEndPayload,
    ContentActionStartEvent,
    ContentActionStartPayload,
    ContentAgentResultEndEvent,
    ContentAgentResultEndPayload,
    ControlInterruptEvent,
    ControlInterruptPayload,
    ControlRollbackEvent,
    ControlRollbackPayload,
    ResumeContext,
    ExecutorMetadata,
    UserInfo,
    RunLifecycleCreatedEvent,
    RunLifecycleCreatedPayload,
    RunLifecycleSuspendedEvent,
    RunLifecycleSuspendedPayload,
    RunLifecycleResumingEvent,
    RunLifecycleResumingPayload,
)
from turbo_agent_core.utils.trace_event_aggregator import TraceEventAggregator


class TestTraceEventAggregator(unittest.TestCase):
    BASE_TS = 1700000000000

    def _find_trace_node(self, snapshot: dict, trace_id: str) -> dict | None:
        for n in snapshot.get("trace_nodes") or []:
            if n.get("trace_id") == trace_id:
                return n
        return None

    def _find_run(self, trace_node: dict, run_id: str) -> dict | None:
        for r in trace_node.get("runs") or []:
            if r.get("run_id") == run_id:
                return r
        return None

    def _find_flow(self, run: dict, flow_type: str, action_id: str | None = None) -> dict | None:
        for f in run.get("data_flows") or []:
            if f.get("type") != flow_type:
                continue
            data = f.get("data") or {}
            if action_id is not None and data.get("action_id") != action_id:
                continue
            return f
        return None

    def test_nested_tree_and_agent_result(self):
        agg = TraceEventAggregator(root_trace_id="R")

        exec_meta = ExecutorMetadata(id="exec", name="exec")
        user_meta = UserInfo(id="u1")

        agg.on_event(
            RunLifecycleCreatedEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 100,
                executor_id="exec",
                executor_path=["agent_root"],
                executor_metadata=exec_meta,
                user_metadata=user_meta,
                payload=RunLifecycleCreatedPayload(input_data={"k": "v"}),
            )
        )

        agg.on_event(
            RunLifecycleCreatedEvent(
                trace_id="R",
                trace_path=["C1"],
                run_id="run_child",
                timestamp=self.BASE_TS + 150,
                executor_id="exec",
                executor_path=["agent_root", "tool_x"],
                executor_metadata=exec_meta,
                user_metadata=user_meta,
                payload=RunLifecycleCreatedPayload(input_data={"x": 1}),
            )
        )

        agg.on_event(
            ContentAgentResultEndEvent(
                trace_id="R",
                trace_path=["C1"],
                run_id="run_child",
                timestamp=self.BASE_TS + 200,
                executor_id="exec",
                payload=ContentAgentResultEndPayload(full_result={"ok": True}, status="success"),
            )
        )

        snap = agg.get_tree_snapshot()
        self.assertEqual(snap["root_trace_id"], "R")

        root = self._find_trace_node(snap, "R")
        self.assertIsNotNone(root)
        self.assertEqual(root["trace_id"], "R")

        child = self._find_trace_node(snap, "C1")
        self.assertIsNotNone(child)
        self.assertEqual(child["parent_trace_id"], "R")
        self.assertIn("C1", root.get("children_trace_ids") or [])

        child_run = self._find_run(child, "run_child")
        self.assertIsNotNone(child_run)

        # run 聚合：状态字段存在
        self.assertIn("keepalive_timestamps", child_run)
        self.assertIsInstance(child_run["keepalive_timestamps"], list)

        # lifecycle 语义字段：created 必须携带 input_data
        self.assertEqual(child_run["input_data"], {"x": 1})
        self.assertIsNone(child_run["resume_context"])

        # agent_result 作为 data_flows 的一条流落在 run 里
        flow = self._find_flow(child_run, "agent_result")
        self.assertIsNotNone(flow)
        self.assertEqual(flow["data"]["full_result"], {"ok": True})

    def test_action_args_and_result(self):
        agg = TraceEventAggregator(root_trace_id="R")

        agg.on_event(
            ContentActionStartEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 100,
                executor_id="exec",
                action_id="a1",
                payload=ContentActionStartPayload(name="search", call_type="TOOL"),
            )
        )

        agg.on_event(
            ContentActionDeltaEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 110,
                executor_id="exec",
                action_id="a1",
                payload=ContentActionDeltaPayload(part="args", delta="h", key_path=["q"]),
            )
        )
        agg.on_event(
            ContentActionDeltaEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 120,
                executor_id="exec",
                action_id="a1",
                payload=ContentActionDeltaPayload(part="args", delta="i", key_path=["q"]),
            )
        )

        agg.on_event(
            ContentActionEndEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 130,
                executor_id="exec",
                action_id="a1",
                payload=ContentActionEndPayload(arguments={"q": "hi"}),
            )
        )

        agg.on_event(
            ContentActionResultEndEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 140,
                executor_id="exec",
                action_id="a1",
                payload=ContentActionResultEndPayload(full_result={"items": [1, 2]}, status="success"),
            )
        )

        snap = agg.get_tree_snapshot()
        root = self._find_trace_node(snap, "R")
        self.assertIsNotNone(root)
        root_run = self._find_run(root, "run_root")
        self.assertIsNotNone(root_run)

        action_call = self._find_flow(root_run, "action_call", action_id="a1")
        self.assertIsNotNone(action_call)
        self.assertEqual(action_call["data"]["action"]["full_arguments"], {"q": "hi"})
        self.assertEqual(action_call["data"]["action"]["arguments"], {"q": "hi"})
        self.assertEqual(action_call["data"]["result"]["full_result"], {"items": [1, 2]})

    def test_interrupt_suspend_resume(self):
        agg = TraceEventAggregator(root_trace_id="R")

        agg.on_event(
            ControlInterruptEvent(
                trace_id="R",
                run_id="run_root_1",
                timestamp=self.BASE_TS + 100,
                executor_id="exec",
                payload=ControlInterruptPayload(
                    interrupt_id="i1",
                    type="approval",
                    reason="need confirm",
                    resume_token="token-1",
                ),
            )
        )

        agg.on_event(
            RunLifecycleSuspendedEvent(
                trace_id="R",
                run_id="run_root_1",
                timestamp=self.BASE_TS + 110,
                executor_id="exec",
                payload=RunLifecycleSuspendedPayload(reason="need confirm"),
            )
        )

        agg.on_event(
            RunLifecycleResumingEvent(
                trace_id="R",
                # 语义约定：挂起后的恢复/重试属于同一 trace 的一次“新的 run”
                run_id="run_root_2",
                timestamp=self.BASE_TS + 120,
                executor_id="exec",
                payload=RunLifecycleResumingPayload(
                    resume_context=ResumeContext(
                        conversation_id="c1",
                        breakpoint_trace_id="R",
                        breakpoint_type="message",
                    )
                )
            )
        )

        snap = agg.get_tree_snapshot()
        root = self._find_trace_node(snap, "R")
        self.assertIsNotNone(root)
        run1 = self._find_run(root, "run_root_1")
        run2 = self._find_run(root, "run_root_2")
        self.assertIsNotNone(run1)
        self.assertIsNotNone(run2)

        self.assertEqual(run1["status"], "suspended")
        self.assertEqual([h["status"] for h in run1["history"]], ["suspended"])

        # interrupt 走 control/control_history
        self.assertIsNotNone(run1["control"]["latest_interrupt"])
        self.assertEqual(run1["control"]["latest_interrupt"]["interrupt_id"], "i1")
        self.assertEqual(len(run1["control_history"]), 1)
        self.assertEqual(run1["control_history"][0]["event_type"], "control.interrupt")

        self.assertEqual(run2["status"], "resuming")
        self.assertEqual([h["status"] for h in run2["history"]], ["resuming"])
        self.assertIsNotNone(run2["resume_context"])

    def test_rollback(self):
        agg = TraceEventAggregator(root_trace_id="R")

        agg.on_event(
            ContentAgentResultEndEvent(
                trace_id="R",
                trace_path=["C1"],
                run_id="run_child",
                timestamp=self.BASE_TS + 300,
                executor_id="exec",
                payload=ContentAgentResultEndPayload(full_result={"v": 1}, status="success"),
            )
        )
        snap0 = agg.get_tree_snapshot()

        root0 = self._find_trace_node(snap0, "R")
        self.assertIsNotNone(root0)
        child0 = self._find_trace_node(snap0, "C1")
        self.assertIsNotNone(child0)
        run0 = self._find_run(child0, "run_child")
        self.assertIsNotNone(run0)
        flow0 = self._find_flow(run0, "agent_result")
        self.assertIsNotNone(flow0)
        self.assertEqual(flow0["data"]["full_result"], {"v": 1})

        agg.on_event(
            ControlRollbackEvent(
                trace_id="R",
                run_id="run_root",
                timestamp=self.BASE_TS + 400,
                executor_id="exec",
                payload=ControlRollbackPayload(target_timestamp=self.BASE_TS + 200, reason="redo"),
            )
        )

        snap1 = agg.get_tree_snapshot()
        root1 = self._find_trace_node(snap1, "R")
        self.assertIsNotNone(root1)
        self.assertIsNone(self._find_trace_node(snap1, "C1"))
        self.assertNotIn("C1", root1.get("children_trace_ids") or [])



if __name__ == "__main__":
    unittest.main()
