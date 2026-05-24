import { motion } from 'framer-motion';

export default function ScrollReveal({ children, direction = 'up', delay = 0, className = '' }) {
  const offsets = { up: { x: 0, y: 40 }, left: { x: -40, y: 0 }, right: { x: 40, y: 0 } };
  const { x, y } = offsets[direction] || offsets.up;

  return (
    <motion.div
      initial={{ opacity: 0, x, y }}
      whileInView={{ opacity: 1, x: 0, y: 0 }}
      viewport={{ once: true, margin: '-50px' }}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.1, 0.25, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
