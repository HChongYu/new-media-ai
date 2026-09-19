<script lang="ts">
import { defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'BackButton',
  props: {
    to: {
      // -1 为默认哨兵值，表示执行 history.back()
      type: [String, Object, Number],
      default: -1
    },
    text: {
      type: String,
      default: '返回'
    }
  },
  emits: ['click'],
  setup(props, { emit }) {
    const router = useRouter()
    const handleClick = () => {
      emit('click')
      if (props.to === -1) {
        history.back()
      } else {
        router.push(props.to as string | Record<string, unknown>)
      }
    }

    return () =>
      h(
        'button',
        {
          class: 'back-button',
          onClick: handleClick
        },
        [
          h(ArrowLeft, { class: 'icon' }),
          h('span', props.text)
        ]
      )
  }
})
</script>
