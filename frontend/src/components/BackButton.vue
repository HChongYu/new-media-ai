import { defineComponent, h } from 'vue'
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
    const handleClick = () => {
      emit('click')
      if (props.to === -1) {
        history.back()
      } else {
        // TODO: 路由跳转
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
