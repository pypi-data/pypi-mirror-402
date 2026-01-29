from cuipyd.ipane import IPane
from cuipyd.logging import log
from cuipyd.layouts.layout import BaseLayout
from cuipyd.mouse import MouseEvent


class DirectionalLayout(BaseLayout):

    def __init__(
        self,
        name=None,
        max_height=None,
        min_height=None,
        max_width=None,
        min_width=None,
    ):
        super().__init__(
            name=name,
            max_height=max_height,
            min_height=min_height,
            max_width=max_width,
            min_width=min_width,
        )
        self._children = []
        self._weights = []
        self._horizontal = True

    @property
    def _max_height(self):
        if self._horizontal:
            if not self._children:
                return self._max_height_val
            max_heights = [x._max_height for x in self._children]
            if any(max_heights):
                return min([x for x in max_heights if x])
        return self._max_height_val

    @property
    def _min_height(self):
        if self._horizontal:
            if not self._children:
                return self._min_height_val
            min_heights = [x._min_height for x in self._children]
            if any(min_heights):
                return max([x for x in min_heights if x])
        return self._min_height_val

    @property
    def _max_width(self):
        if not self._horizontal:
            if not self._children:
                return self._max_width_val
            max_widths = [x._max_width for x in self._children]
            if any(max_widths):
                return min([x for x in max_widths if x])
        return self._max_width_val

    @property
    def _min_width(self):
        if not self._horizontal:
            if not self._children:
                return self._min_width_val
            min_widths = [x._min_width for x in self._children]
            if any(min_widths):
                return max([x for x in min_widths if x])
        return self._min_width_val

    def _add_child(self, child: IPane, **kwargs):
        if kwargs.get("weight", False):
            self._weights.append(int(kwargs["weight"]))
        else:
            self._weights.append(1)
        super()._add_child(child, **kwargs)
        self._resize()

    def _update_window_size(self, rows, cols, r_pos, c_pos):
        super()._update_window_size(rows, cols, r_pos, c_pos)
        self._resize()

    def _resize(self):
        y, x = self._get_raw_size()
        if self._shift_down_from_title():
            y -= 1

        if self._horizontal:
            screen_sizes = self._get_pane_sizes(
                x, self._weights, self._children, vertical=False
            )
            start_col = 0
            row_pos = 0
            if self._shift_down_from_title():
                row_pos += 1
            for i in range(len(self._children)):
                child = self._children[i]
                width = screen_sizes[i]
                child._update_window_size(y, width, row_pos, start_col)
                start_col += width
        else:
            screen_sizes = self._get_pane_sizes(
                y, self._weights, self._children, vertical=True
            )
            start_row = 0
            if self._shift_down_from_title():
                start_row += 1
            for i in range(len(self._children)):
                child = self._children[i]
                height = screen_sizes[i]
                child._update_window_size(height, x, start_row, 0)
                start_row += height

    @staticmethod
    def _get_pane_sizes(size, weights, children, vertical=False):
        output_sizes = DirectionalLayout._get_start_weights(size, weights, children)
        start_sizes = [x for x in output_sizes]

        if len(children) == 1:
            return [size]

        mins = []
        maxs = []
        if vertical:
            mins = [c._min_height for c in children]
            maxs = [c._max_height for c in children]
        else:
            mins = [c._min_width for c in children]
            maxs = [c._max_width for c in children]

        # Adjust for minimums
        for min_index in range(len(mins)):
            min_val = mins[min_index]

            # No minimum size specified
            if min_val is None:
                continue

            # Less than min index, need to make bigger and remove size from others
            if output_sizes[min_index] < min_val:
                output_sizes[min_index] = min_val

                check_index = 0

                while sum(output_sizes) != size:
                    new_check_size = output_sizes[check_index] - 1
                    if check_index == min_index or (
                        mins[check_index] != None and new_check_size < mins[check_index]
                    ):
                        check_index = (check_index + 1) % len(output_sizes)
                        continue

                    output_sizes[check_index] = new_check_size
                    check_index = (check_index + 1) % len(output_sizes)

        # Adjust for minimums
        for max_index in range(len(maxs)):
            max_val = maxs[max_index]

            # No minimum size specified
            if max_val is None:
                continue

            # Less than min index, need to make bigger and remove size from others
            if output_sizes[max_index] > max_val:
                output_sizes[max_index] = max_val

                check_index = 0

                while sum(output_sizes) != size:
                    new_check_size = output_sizes[check_index] + 1
                    if check_index == max_index or (
                        maxs[check_index] != None and new_check_size > maxs[check_index]
                    ):
                        check_index = (check_index + 1) % len(output_sizes)
                        continue

                    output_sizes[check_index] = new_check_size
                    check_index = (check_index + 1) % len(output_sizes)

        return output_sizes

    @staticmethod
    def _get_start_weights(size, weights, children):
        if len(children) == 0:
            return []

        total_weight = sum(weights)

        base_val = size // total_weight
        output_sizes = []
        for w in weights:
            output_sizes.append(w * base_val)

        total_size = sum(output_sizes)
        if total_size < size:
            diff = size - total_size
            for i in range(diff):
                output_sizes[i % len(output_sizes)] += 1

        return output_sizes


class HLayout(DirectionalLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _register_mouse_event(self, mouse_event):
        row = mouse_event.row
        column = mouse_event.column

        log(str(column) + " " + str(row))
        if not self._children:
            return

        y, x = self._get_raw_size()
        screen_sizes = self._get_pane_sizes(
            x, self._weights, self._children, vertical=False
        )

        screen_index = 0

        while column >= sum(screen_sizes[: screen_index + 1]):
            screen_index += 1

        mouse_event.column -= sum(screen_sizes[:screen_index])

        log(str(column) + " " + str(row) + "Child: " + str(screen_index))
        # self._children[screen_index]._register_mouse_event(mouse_event)
        clear_event = MouseEvent.get_null()
        for i in range(len(self._children)):
            child = self._children[i]
            if i == screen_index:
                if child._shift_down_from_title():
                    new_r, new_c = child._tweak_row_col(
                        mouse_event.row, mouse_event.column, reverse=True
                    )
                    mouse_event.row = new_r
                    mouse_event.column = new_c
                child._register_mouse_event(mouse_event)
            else:
                child._register_mouse_event(clear_event)


class VLayout(DirectionalLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._horizontal = False

    def _register_mouse_event(self, mouse_event):
        row = mouse_event.row
        column = mouse_event.column
        if not self._children:
            return

        y, x = self._get_raw_size()
        if self._shift_down_from_title():
            y -= 1
        screen_sizes = self._get_pane_sizes(
            y, self._weights, self._children, vertical=True
        )

        screen_index = 0

        while row >= sum(screen_sizes[: screen_index + 1]):
            screen_index += 1
        mouse_event.row -= sum(screen_sizes[:screen_index])

        # log(str(column) + " " + str(row) + "Child: " + str(screen_index))
        # self._children[screen_index]._register_mouse_event(mouse_event)

        clear_event = MouseEvent.get_null()
        for i in range(len(self._children)):
            child = self._children[i]
            if i == screen_index:
                if child._shift_down_from_title():
                    new_r, new_c = child._tweak_row_col(
                        mouse_event.row, mouse_event.column, reverse=True
                    )
                    mouse_event.row = new_r
                    mouse_event.column = new_c
                child._register_mouse_event(mouse_event)
            else:
                child._register_mouse_event(clear_event)

        self._refresh()
