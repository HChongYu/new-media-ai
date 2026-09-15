<script>
import { defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

export default defineComponent({
  name: 'BackButton',
  props: {
    to: {
      type: [String, Object],
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
        router.push(props.to)
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
